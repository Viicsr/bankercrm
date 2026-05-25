from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _get_async_db_url(url: str) -> str:
    """Convierte postgresql:// a postgresql+asyncpg:// para Railway."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(
    _get_async_db_url(settings.DATABASE_URL),
    echo=settings.APP_ENV == "development",  # muestra las consultas SQL en la consola
    pool_size=5,  # tamaño del pool de conexiones
    max_overflow=10,  # número máximo de conexiones que se pueden crear
    pool_pre_ping=True,  # detecta conexiones muertas antes de usarlas
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # función para obtener una sesión de la base de datos
    async with AsyncSessionLocal() as session:  # crea una sesión de la base de datos
        yield session  # retorna la sesión de la base de datos
