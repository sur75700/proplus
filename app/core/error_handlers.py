from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


REQUEST_ID_HEADER = "X-Request-ID"


def _request_id(request: Request) -> str:
    existing = request.headers.get(REQUEST_ID_HEADER)
    return existing if existing else str(uuid4())


async def request_id_middleware(request: Request, call_next):
    rid = _request_id(request)
    request.state.request_id = rid

    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = rid

    return response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        rid = getattr(request.state, "request_id", _request_id(request))

        return JSONResponse(
            status_code=exc.status_code,
            headers={REQUEST_ID_HEADER: rid},
            content={
                "error": {
                    "code": "http_error",
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "request_id": rid,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        rid = getattr(request.state, "request_id", _request_id(request))

        return JSONResponse(
            status_code=422,
            headers={REQUEST_ID_HEADER: rid},
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "status_code": 422,
                    "request_id": rid,
                    "details": exc.errors(),
                }
            },
        )
