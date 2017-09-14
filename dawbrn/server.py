import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import traceback

import aiohttp
import aiohttp.web

from . import build
from . import exception

logger = logging.getLogger(__name__)

def create_log_context_id():
    return base64.b32encode(os.urandom(20)).decode("ascii").lower()

def create_traceback_id():
    tb = traceback.format_exc()
    h = hashlib.md5()
    h.update(tb.encode("utf-8"))
    return h.hexdigest()

def exception_to_obj(exception):
    traceback_id = create_traceback_id()
    error = {
        "error_type": exception.__class__.__name__,
        "error_traceback": traceback_id,
    }
    return (traceback_id, error)

def log_traceback_multi_line():
    text = traceback.format_exc()
    for line in text.split("\n"):
        if line != "":
            logger.error(line)

#
# Handlers
#

def json_endpoint(coro):
    async def handler(request):
        asyncio.Task.current_task().log_context = create_log_context_id()

        try:
            spec = await request.json()
        except ValueError:
            logger.error("Rejected {method} {path}: body is not parsable as json".format(
                method=request.method,
                path=request.path,
            ))
            return aiohttp.web.Response(
                status=400,
                content_type="application/json",
                text=json.dumps(
                    obj=[{
                        "error_message": "expected json",
                        "error_type": "json parsability",
                        "path": [],
                    }],
                    ensure_ascii=False,
                ),
            )

        try:
            ret = await coro(spec, request)
        except exception.ClientError as e:
            status = 400
            logger.error("({e.__class__.__name__}): {e.desc}".format(**locals()))
        except Exception as e:
            status = 500
            traceback_id, obj = exception_to_obj(e)
            logger.error("Internal failure ({e.__class__.__name__}), traceback hash: {traceback_id}".format(**locals()))
            log_traceback_multi_line()
        else:
            status = 200
            obj = ret

        response = aiohttp.web.Response(
            status=status,
            content_type="application/json",
            text=json.dumps(
                obj=obj,
                ensure_ascii=False,
            ),
        )
        return response
    return handler

def _github_deploy_url(stub):
    return "https://{}@github.com/{}.git".format(
        os.environ["GITHUB_TOKEN"],
        stub,
    )

def _github_pages_url(stub, deploy_dir):
    username, reponame = stub.split("/", 1)
    return "https://{username}.github.io/{reponame}/{deploy_dir}".format(**locals())

class GithubCommentStatus(object):
    def __init__(self, repo, pr_num, sha, success_url):
        self.repo = repo
        self.pr_num = pr_num
        self.sha = sha
        self.success_url = success_url
        self.result = None
        self.github = "https://api.github.com"
        self.session = None

    async def add_comment(self, state, body):
        logger.debug("Adding comment state {state} for PR {self.pr_num}, commit {self.sha}".format(**locals()))

        async with self.session.post(
            "{self.github}/repos/{self.repo}/issues/{self.pr_num}/comments".format(**locals()),
            json={
                "body": body,
            },
            headers={
                "Authorization": "token {}".format(os.environ["GITHUB_TOKEN"]),
            },
        ) as response:
            async with response:
                if response.status // 100 == 2:
                    logger.info("Added comment state {state} for PR {self.pr_num}".format(**locals()))
                else:
                    logger.error("Unable to add comment state {state} for PR, HTTP {response.status}".format(**locals()))

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        shortsha = self.sha[:8]
        if exc_type is None:
            if self.result is build.Result.WARNING:
                body = "[Build completed with warnings]({self.success_url}) (commit {shortsha}) [Full Log]({self.success_url}/dawbrn.log)"
                state = "success"
            elif self.result is build.Result.FAILURE:
                body = "[Build failed]({self.success_url}) (commit {shortsha}) [Full Log]({self.success_url}/dawbrn.log)"
                state = "success"
            else:
                body = "[Build completed ok]({self.success_url}) (commit {shortsha}) [Full Log]({self.success_url}/dawbrn.log)"
                state = "failure"
            await self.add_comment(state, body.format(**locals()))
        else:
            await self.add_comment("error", "Internal error (commit {shortsha}): {exc_type.__name__}".format(**locals()))
        await self.session.__aexit__(exc_type, exc_value, exc_traceback)

def background_done_callback(future):
    try:
        future.result()
    except exception.ClientError as e:
        traceback_id, obj = exception_to_obj(e)
        logger.error("({e.__class__.__name__}): {e.desc}, traceback hash: {traceback_id}".format(**locals()))
        log_traceback_multi_line()
    except Exception as e:
        traceback_id, obj = exception_to_obj(e)
        logger.error("Internal failure ({e.__class__.__name__}), traceback hash: {traceback_id}".format(**locals()))
        log_traceback_multi_line()

async def github_webhook(data, request):
    # Verify signature
    hasher = hmac.new(os.environ["GITHUB_HMAC_TOKEN"].encode("utf-8"), digestmod="sha1")
    hasher.update(await request.read())
    expected = "sha1={}".format(hasher.hexdigest())
    if not hmac.compare_digest(expected, request.headers["X-Hub-Signature"]):
        raise exception.ClientError("Invalid Github signature")

    logger.info("Received {} event".format(request.headers["X-GitHub-Event"]))

    bgtask = request.app.loop.create_task(github_webhook_background(data, request))
    bgtask.log_context = asyncio.Task.current_task().log_context
    bgtask.add_done_callback(background_done_callback)

    return {}

async def github_webhook_background(data, request):
    if request.headers["X-GitHub-Event"] == "ping":
        pass

    elif request.headers["X-GitHub-Event"] == "push":
        if data["ref"] in ["refs/heads/master", "refs/heads/asciidoctor-mvn"]:
            trimmed_ref = data["ref"][11:]
            logger.info("Building branch {trimmed_ref} from repo {data[repository][full_name]}".format(**locals()))
            deploy_dir = "dev/{trimmed_ref}".format(**locals())
            await build.build_deploy(
                source_url=data["repository"]["html_url"],
                source_ref=trimmed_ref,
                deploy_dir=deploy_dir,
                deploy_url=_github_deploy_url(os.environ["GITHUB_PAGES_STUB"]),
            )
        else:
            logger.debug("Ignoring branch: {data[ref]}".format(**locals()))

    elif request.headers["X-GitHub-Event"] == "create":
        if data["ref_type"] == "tag":
            logger.info("Building tag {data[ref]} from repo {data[repository][full_name]}".format(**locals()))
            await build.build_deploy(
                source_url=data["repository"]["html_url"],
                source_ref=data["ref"],
                deploy_dir=data["ref"],
                deploy_url=_github_deploy_url(os.environ["GITHUB_PAGES_STUB"]),
            )
        else:
            logger.debug("Ignoring ref_type: {data[ref_type]}".format(**locals()))

    elif request.headers["X-GitHub-Event"] == "pull_request":
        if data["action"] in ["opened", "reopened", "synchronize"]:
            logger.info("PR #{data[number]} new/updated, building branch {data[pull_request][head][ref]} from repo {data[pull_request][head][repo][full_name]}".format(**locals()))
            deploy_dir = "PR/{data[number]}".format(**locals())
            async with GithubCommentStatus(
                repo=data["repository"]["full_name"],
                pr_num=data["number"],
                sha=data["pull_request"]["head"]["sha"],
                success_url=_github_pages_url(os.environ["GITHUB_PAGES_PR_STUB"], deploy_dir),
            ) as status:
                status.result = await build.build_deploy(
                    source_url=data["pull_request"]["head"]["repo"]["html_url"],
                    source_ref=data["pull_request"]["head"]["ref"],
                    deploy_dir=deploy_dir,
                    deploy_url=_github_deploy_url(os.environ["GITHUB_PAGES_PR_STUB"]),
                )
        elif data["action"] == "closed":
            logger.info("PR #{data[number]} closed, removing".format(**locals()))
            await build.build_undeploy(
                deploy_dir="PR/{data[number]}".format(**locals()),
                deploy_url=_github_deploy_url(os.environ["GITHUB_PAGES_PR_STUB"]),
            )
        else:
            logger.debug("Ignoring action: {data[action]}".format(**locals()))
    else:
        raise Exception("Unknown event type")

    logger.info("Event handled successfully".format(**locals()))

async def show_id(request):
    asyncio.Task.current_task().log_context = create_log_context_id()
    return aiohttp.web.Response(
        content_type="text/plain",
        text="Dawbrn",
    )

#
# Setup
#

def start_server(bind):
    logger.debug("Starting server")

    app = aiohttp.web.Application()

    logger.debug("Setting up handlers")
    app.router.add_route(
        "GET",
        "/",
        show_id,
    )
    app.router.add_route(
        "POST",
        "/github",
        json_endpoint(github_webhook),
    )

    logger.debug("Handing over thread to run_app")
    aiohttp.web.run_app(
        app,
        host=bind[0],
        port=bind[1],
    )
