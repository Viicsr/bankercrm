from contextlib import asynccontextmanager
import logging, asyncio
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine,get_db
from app.api.v1.routers import clients, accounts, auth
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Contexto de vida de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting app | ENV: {settings.APP_ENV}")
    yield
    await engine.dispose()
    logger.info("Database disconnected")

# Creación de la aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    lifespan=lifespan
)

# Endpoint de salud de la aplicación
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await asyncio.wait_for(
            db.execute(text("SELECT 1")),
            timeout=5.0
        )
        db_status = "connected"
    except asyncio.TimeoutError:
        return JSONResponse(status_code=503, content={
            "status": "error", 
            "db": "timeout",
            "version": settings.APP_VERSION, 
            "environment": settings.APP_ENV
        })
    except Exception:
        return JSONResponse(status_code=503, content={
            "status": "error", 
            "db": "unreachable",
            "version": settings.APP_VERSION, 
            "environment": settings.APP_ENV
        })
    return {
        "status": "ok", 
        "db": db_status,
        "version": settings.APP_VERSION, 
        "environment": settings.APP_ENV
    }

# Incluye el router de clientes en la aplicación
app.include_router(clients.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")