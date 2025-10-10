import json
import typing

from loguru import logger
from pydantic import ValidationError
from aiohttp.web_exceptions import HTTPUnprocessableEntity, HTTPException
from aiohttp_session import get_session
from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware

from app.web.utils import error_json_response

if typing.TYPE_CHECKING:
    from app.web.app import Application, Request


HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "not_implemented",
    409: "conflict",
    500: "internal_server_error",
}


@middleware
async def error_handling_middleware(request: "Request", handler):
    try:
        response = await handler(request)
    except HTTPUnprocessableEntity as e:
        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message=e.reason,
            data=json.loads(e.text),
        )
    except ValidationError as e:
        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message="Unprocessable Entity",
            data={'json': {'login': ['Missing data for required field.']}},
        )
    # except HTTPException as e:
    #     return error_json_response(http_status=e.status, status='HTTP error', message=str(e))
    # except Exception as e:
    #     return error_json_response(http_status=500, status='internal server error', message=str(e))

    return response


@middleware
async def auth_middleware(request, handler):
    if request.path == "/admin.login":
        return await handler(request)
    logger.debug(f"request {request}")

    session = await get_session(request)
    logger.debug(f"session {session}")
    
    admin = session.get("admin")
    logger.debug(f"admin {admin}")

    if not admin:
        return error_json_response(
            http_status=401,
            status="unauthorized",
            message="You must be logged in"
        )

    request["admin"] = admin
    return await handler(request)


def setup_middlewares(app: "Application"):
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(validation_middleware)
    app.middlewares.append(auth_middleware)
