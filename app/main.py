import asyncio
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.routers import accounts, auth, clients
from app.core.config import settings
from app.core.database import engine
from app.core.error_handlers import (
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.exceptions import AppBaseException
from app.core.logging_config import setup_logging
from app.middleware.request_id import RequestLoggingMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.schemas.errors import HealthResponse

# Antes de crear la instancia de FastAPI
setup_logging()

logger = logging.getLogger(__name__)


# Contexto de vida de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = settings
    logger.info(f"Starting app | ENV: {settings.APP_ENV}")
    yield
    await engine.dispose()
    logger.info("Database disconnected")


openapi_tags = [
    {
        "name": "Auth",
        "description": "User registration, login, and token refresh endpoints.",
    },
    {
        "name": "Clients",
        "description": "Client management endpoints with RBAC protection.",
    },
    {
        "name": "Accounts",
        "description": "Bank account management endpoints linked to clients.",
    },
    {
        "name": "System",
        "description": "Operational endpoints such as health checks.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Banking Customer Relationship Manager

REST API for managing banking clients and accounts.
Built with **FastAPI**, **PostgreSQL**, and **JWT authentication with RBAC**.

---

### Quick start

1. **Register** — `POST /api/v1/auth/register`
2. **Login** — `POST /api/v1/auth/login` → copy the `access_token`
3. Click **Authorize** at the top of this page and enter: `Bearer <your_token>`

All protected endpoints return **401** if the token is missing or expired,
and **403** if your role does not have permission.

---

### Roles

| Role | Permissions |
|---|---|
| `admin` | Full read + write access |
| `analyst` | Read + create clients and accounts |
| `read_only` | Read only |

---

### Standard error format

Every error response follows this structure:

```json
{
  "error": "NotFoundError",
  "detail": "Client '42' not found",
  "path": "/api/v1/clients/42",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Validation errors (422) additionally include an `errors` array with per-field details.

---

### Correlation IDs

Every request receives a unique `X-Request-ID` header in the response.
The same ID appears in the `request_id` field of any error body.
Use it to cross-reference logs when reporting issues.
""",
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    openapi_tags=openapi_tags,
    contact={
        "name": "Victor Santos",
        "url": "https://github.com/Viicsr",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
)


# Endpoint de salud de la aplicación
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description=(
        "Returns the operational status of the API and its database connection. "
        "Used by Docker, Railway, and any load balancer health probe. "
        "Returns **503** if the database is unreachable or times out after 5 seconds. "
        "Does **not** require authentication."
    ),
    responses={
        200: {"description": "API and database are healthy"},
        503: {"description": "Database unreachable or timed out"},
    },
)
async def health_check():
    db_status = "ok"
    db_latency_ms = None

    try:
        start = time.perf_counter()
        async with engine.begin() as conn:
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=5.0,
            )
        db_latency_ms = round((time.perf_counter() - start) * 1000, 2)
    except TimeoutError:
        db_status = "unavailable"
    except Exception:
        db_status = "degraded"

    overall_status = "ok" if db_status == "ok" else "degraded"
    http_status = 200 if overall_status == "ok" else 503

    return JSONResponse(
        status_code=http_status,
        content={
            "status": overall_status,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "dependencies": {
                "database": {
                    "status": db_status,
                    "latency_ms": db_latency_ms,
                }
            },
        },
    )


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
