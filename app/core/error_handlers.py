import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import AppBaseException

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    logger.warning(
        "Application error",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.detail,
            "path": request.url.path,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"field": " -> ".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    logger.info("Validation error", extra={"errors": errors, "path": request.url.path})
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "detail": "Request validation failed",
            "errors": errors,
            "path": request.url.path,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Nunca expones el traceback al cliente — lo logas internamente
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={"path": request.url.path, "method": request.method},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred",
            "path": request.url.path,
        },
    )