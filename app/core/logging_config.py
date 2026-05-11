import json
import logging
import sys
from datetime import UTC, datetime

from asgi_correlation_id.context import correlation_id

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Formatea cada log como una línea JSON — listo para ingestión en Datadog/CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "request_id": correlation_id.get() or "-",
        }

        # Añade campos extra si los hay (pasados con extra={} en el logger)
        for key, value in record.__dict__.items():
            if key not in {
                "timestamp",
                "level",
                "logger",
                "message",
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                log_entry[key] = value

        # Añade traceback si hay excepción
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class DevFormatter(logging.Formatter):
    """Formato legible para desarrollo que incluye campos extra del middleware."""

    EXTRA_FIELDS = {"method", "path", "status_code", "duration_ms"}

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = {k: v for k, v in record.__dict__.items() if k in self.EXTRA_FIELDS}
        if extras:
            extra_str = " | " + " ".join(f"{k}={v}" for k, v in extras.items())
            return base + extra_str
        return base


def setup_logging() -> None:
    log_level = logging.DEBUG if settings.APP_ENV == "development" else logging.INFO

    # Formato según entorno: JSON en producción, legible en desarrollo
    if settings.APP_ENV == "development":
        formatter = DevFormatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        formatter = JSONFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configura el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    # Silencia loggers verbosos de librerías externas
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.APP_ENV == "development" else logging.WARNING
    )
    logging.getLogger("sqlalchemy.engine").propagate = False
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("python_multipart").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)
