import asyncio
import base64
import hashlib
import json
import logging
import os
import traceback

import aiohttp
import aiohttp.web

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
            logger.info("Completed ok")

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

async def github_webhook(data, request):
    # Verify signature
    hasher = hmac.new(os.environ["GITHUB_HMAC_TOKEN"], digestmod="sha1")
    hasher.update(await request.read())
    expected = "sha1={}".format(hasher.hexdigest())
    if not hmac.compare_digest(expected, request.headers["X-Hub-Signature"]):
        raise exception.ClientError("Invalid Github signature")

    logger.info("Received {} event".format(request.headers["X-GitHub-Event"]))

    if request.headers["X-GitHub-Event"] == "ping":
        pass

    elif request.headers["X-GitHub-Event"] == "push":
        if data["ref"] == "refs/heads/master":
            trimmed_ref = data["ref"][11:]
            logger.info("Building branch {trimmed_ref} from repo {data[repository][full_name]}".format(**locals()))
            await build_deploy(
                source_url=data["repository"]["html_url"],
                source_ref=data["ref"],
                deploy_dir="dev/{trimmed_ref}".format(**locals()),
                deploy_url=_github_deploy_url(os.environ["GITHUB_PAGES_STUB"]),
            )
        else:
            logger.debug("Ignoring branch {data[ref]}".format(**locals()))

    elif request.headers["X-GitHub-Event"] == "create":
        if data["ref_type"] == "tag":
            logger.info("Building tag {data[ref]} from repo {data[repository][full_name]}".format(**locals()))
            await build_deploy(
                source_url=data["repository"]["html_url"],
                source_ref=data["ref"],
                deploy_dir=data["ref"],
                deploy_url=_github_deploy_url(os.environ["GITHUB_PAGES_STUB"]),
            )
        else:
            logger.debug("Ignoring ref_type: {data[ref_type]}".format(**locals()))

    elif request.headers["X-GitHub-Event"] == "pull_request":
        pass
        await build_deploy(
            TODOcommit,
            deploy_dir="PR/TODOprnumber",
            deploy_url=_github_deploy_url(os.environ["GITHUB_PAGES_PR_STUB"]),
            cleanup=True,
        )
    else:
        raise Exception("Unknown event type")

    return {}

async def show_id(request):
    asyncio.Task.current_task().log_context = create_log_context_id()
    return aiohttp.web.Response(
        content_type="text/plain",
        text="Dawbrn",
    )

#
# Setup
#

def start_server(bind, mount_root):
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
    aiohttp.web.run_app(app)
