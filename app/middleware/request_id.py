import logging
import time

from asgi_correlation_id.context import correlation_id
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Loga cada petición con su duración y añade X-Request-ID a la respuesta."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        request_id = correlation_id.get()

        logger.info(
            "HTTP Request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "request_id": request_id,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        return response
