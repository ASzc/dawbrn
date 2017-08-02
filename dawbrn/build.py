import asyncio
import asyncio.subprocess
import os
import tempfile

from . import exception

_deploy_tasks = dict()

async def build_deploy(source_url, source_ref, deploy_dir, deploy_url, cleanup=False):
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

    os.makedirs("/tmp/dawbrn", mode=0o700, exist_ok=True)
    with tempfile.TemporaryDirectory(dir="/tmp/dawbrn") as source_clone:
        p = asyncio.create_subprocess_exec(
            "git", "clone",
            "--branch", source_ref,
            "--depth", "1",
            "--", source_url, source_clone,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        if await p.wait() != 0:
            raise exception.SubprocessError("Could not clone {source_ref} from {source_url}".format(**locals()))

        p = asyncio.create_subprocess_exec(
            "sudo", "/usr/bin/dawbrn_dockerbuild",
            source_clone,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        if await p.wait() != 0:
            raise exception.SubprocessError("Docker build failed".format(**locals()))

        # TODO gather and deploy from source_clone
