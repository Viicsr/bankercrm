from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine
from app.api.v1.routers import clients

# Contexto de vida de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        print(f"Database connected | ENV: {settings.APP_ENV}")
    yield
    await engine.dispose()
    print("Database disconnected")

# Creación de la aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    lifespan=lifespan
)

# Endpoint de salud de la aplicación
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }

# Incluye el router de clientes en la aplicación
app.include_router(clients.router, prefix="/api/v1")