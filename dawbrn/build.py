import asyncio
import asyncio.subprocess
import enum
import logging
import os
import tempfile
import time

from . import exception

logger = logging.getLogger(__name__)

class Result(enum.Enum):
    SUCCESS = 1
    WARNING = 2
    FAILURE = 3

_deploy_tasks = dict()

async def register(deploy_dir, deploy_url):
    # Cancel any existing task that deploys to the same place
    if deploy_url not in _deploy_tasks:
        _deploy_tasks[deploy_url] = dict()
    if deploy_dir in _deploy_tasks[deploy_url]:
        other_task = _deploy_tasks[deploy_url][deploy_dir]
        # Register self as the active task now, as we will suspend execution
        # when waiting for the other task to finish.
        _deploy_tasks[deploy_url][deploy_dir] = asyncio.Task.current_task()
        if not other_task.done():
            other_task.cancel()
            await asyncio.wait(other_task)
    else:
        # Register self as the active task for the deployment location
        _deploy_tasks[deploy_url][deploy_dir] = asyncio.Task.current_task()

async def _subprocess(program, *args, msg=None, error_ok=False, output=False):
    p = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdout=asyncio.subprocess.PIPE if output else asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.STDOUT if output else asyncio.subprocess.DEVNULL,
    )
    if output:
        stdout_data, stderr_data = await p.communicate()
        return stdout_data.decode("utf-8").strip()
    if await p.wait() != 0:
        if not error_ok:
            raise exception.SubprocessError(msg or "{program} failed, code {p.returncode}".format(**locals()))
    return p.returncode

async def _try_deploy(deploy_url, coro, commit_msg="Deploy"):
    with tempfile.TemporaryDirectory() as deploy_clone:
        await _subprocess("git", "init", deploy_clone)
        await _subprocess(
            "git", "-C", deploy_clone, "remote", "add", "origin", deploy_url,
        )

        retry_count = 0
        retry = True
        while retry:
            logger.info("Attempt {retry_count} to deploy".format(**locals()))
            await _subprocess(
                "git", "-C", deploy_clone, "fetch",
                "--depth", "1",
                "origin",
                "gh-pages",
                msg="Could not fetch deployment repository",
            )

            await _subprocess("git", "-C", deploy_clone, "reset", "--hard", "origin/gh-pages")
            await _subprocess("git", "-C", deploy_clone, "checkout", "-b", str(time.time()), "origin/gh-pages")

            await coro(deploy_clone)
            await _subprocess("git", "-C", deploy_clone, "add", "-A")
            p = await _subprocess(
                "git", "-C", deploy_clone, "commit", "-m", commit_msg,
                error_ok=True,
            )
            if p != 0:
                logger.info("No changes to commit, skipping push")
                return

            p = await _subprocess(
                "git", "-C", deploy_clone, "push", "origin", "HEAD:gh-pages",
                error_ok=True,
            )
            # There may have been an interleaved push, assume any failure is this scenario and retry
            success = p == 0
            retry = not success and retry_count < 5
            retry_count += 1
            if not success:
                logger.info("Unable to push, retry == {retry}".format(**locals()))
            if retry:
                delay = 2 * (2 ** retry_count - 1)
                logger.debug("Sleeping for {delay} seconds".format(**locals()))
                await asyncio.sleep(delay)
        if not success:
            raise exception.DeployError("Giving up on deploy after {retry_count} attempts".format(**locals()))

async def build_deploy(source_url, source_ref, deploy_dir, deploy_url):
    await register(deploy_dir, deploy_url)

    os.makedirs("/tmp/dawbrn", mode=0o700, exist_ok=True)
    with tempfile.TemporaryDirectory(dir="/tmp/dawbrn") as source_clone:
        await _subprocess(
            "git", "clone",
            "--branch", source_ref,
            "--depth", "1",
            "--", source_url, source_clone,
            msg="Could not clone {source_ref} from {source_url}".format(**locals()),
        )

        log_path = os.path.join(source_clone, "dawbrn.log")
        # https://www.projectatomic.io/blog/2015/08/why-we-dont-let-non-root-users-run-docker-in-centos-fedora-or-rhel/
        try:
            await _subprocess(
                "sudo", "/usr/bin/dawbrn_dockerbuild", source_clone,
                msg="Build failed",
            )
        except exception.SubprocessError as e:
            # Delegate reading to avoid blocking the aio thread
            error_output = await _subprocess(
                "cat",
                log_path,
                output=True,
            )
        else:
            error_output = None

        async def generate_index(d):
            contents = sorted(os.listdir(d))
            # If directory has index already, do not overwrite
            if "index.html" not in contents:
                with open(os.path.join(d, "index.html"), "w") as i:
                    print("<html><body><ul>", file=i)
                    for c in contents:
                        print("<li><a href='{c}'>{c}</a></li>".format(**locals()), file=i)
                    print("</ul></body></html>", file=i)
            # Recurse
            for c in contents:
                cpath = os.path.join(d, c)
                if os.path.isdir(cpath):
                    await generate_index(cpath)

        async def copy(deploy_clone):
            output_dir = os.path.join(deploy_clone, deploy_dir)
            # Not using shutil to avoid blocking the aio thread
            await _subprocess("rm", "-rf", output_dir)
            os.makedirs(output_dir)
            await _subprocess("cp", log_path, output_dir)
            target_dir = os.path.join(source_clone, "target", ".") # TODO configurable???
            if os.path.exists(target_dir):
                await _subprocess("cp", "-r", target_dir, output_dir)
            await generate_index(output_dir)

        await _try_deploy(deploy_url, copy)

        if error_output is not None:
            return Result.FAILURE

        warnings = await _subprocess(
            "grep",
            "-i",
            "-e", "WARNING",
            log_path,
            output=True,
        )
        if len(warnings) > 0:
            return Result.WARNING

        return Result.SUCCESS

async def build_undeploy(deploy_dir, deploy_url):
    await register(deploy_dir, deploy_url)

    async def remove(deploy_clone):
        # Not using shutil to avoid blocking the aio thread
        await _subprocess(
            "rm", "-rf",
            os.path.join(deploy_clone, deploy_dir)
        )
    await _try_deploy(deploy_url, remove, commit_msg="Undeploy")
