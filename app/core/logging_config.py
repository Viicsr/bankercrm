import logging
import logging.config
import json
import sys
from datetime import datetime, timezone
from app.core.config import settings
from asgi_correlation_id.context import correlation_id


class JSONFormatter(logging.Formatter):
    """Formatea cada log como una línea JSON — listo para ingestión en Datadog/CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
                "timestamp", "level", "logger", "message",
                "name", "msg", "args", "levelname", "levelno",
                "pathname", "filename", "module", "exc_info",
                "exc_text", "stack_info", "lineno", "funcName",
                "created", "msecs", "relativeCreated", "thread",
                "threadName", "processName", "process",
            }:
                log_entry[key] = value

        # Añade traceback si hay excepción
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    log_level = logging.DEBUG if settings.APP_ENV == "development" else logging.INFO

    # Formato según entorno: JSON en producción, legible en desarrollo
    if settings.APP_ENV == "development":
        formatter = logging.Formatter(
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
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)