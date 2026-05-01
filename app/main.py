import asyncio
import logging
import re
import uuid
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routers import accounts, auth, clients
from app.core.config import settings
from app.core.database import engine, get_db
from app.core.error_handlers import (
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import AppBaseException
from app.core.logging_config import setup_logging
from app.middleware.request_id import RequestLoggingMiddleware
from app.middleware.security import SecurityHeadersMiddleware

# Antes de crear la instancia de FastAPI
setup_logging()

logger = logging.getLogger(__name__)  # logging.getLogger(__name__) i


# Contexto de vida de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = settings
    logger.info(f"Starting app | ENV: {settings.APP_ENV}")
    yield
    await engine.dispose()
    logger.info("Database disconnected")


# Creación de la aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    lifespan=lifespan,
)


# Endpoint de salud de la aplicación
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=5.0)
        db_status = "connected"
    except TimeoutError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "db": "timeout",
                "version": settings.APP_VERSION,
                "environment": settings.APP_ENV,
            },
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "db": "unreachable",
                "version": settings.APP_VERSION,
                "environment": settings.APP_ENV,
            },
        )
    return {
        "status": "ok",
        "db": db_status,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


# Incluye el router de clientes en la aplicación
app.include_router(clients.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")

# Agrega los manejadores de excepciones
app.add_exception_handler(AppBaseException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

UUID4_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
# Orden de registro: se ejecutan en orden inverso al registro
# (el último registrado es el primero en ejecutarse)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CorrelationIdMiddleware,
    header_name="X-Request-ID",
    generator=lambda: uuid.uuid4().hex,  # genera UUID4 si el cliente no manda uno
    validator=UUID4_REGEX.match,  # rechaza IDs que no sean UUID4 válidos
    transformer=lambda a: a,  # devuelve el ID tal cual
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
