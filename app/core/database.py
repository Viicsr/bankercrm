from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession 
from sqlalchemy.orm import DeclarativeBase # clase base para las declaraciones de SQLAlchemy (ORM) 
from app.core.config import settings # configuración de la aplicación

engine = create_async_engine(
    settings.DATABASE_URL, # URL de la base de datos
    echo=False, # muestra las consultas SQL en la consola
    pool_size=5, # tamaño del pool de conexiones
    max_overflow=10, # número máximo de conexiones que se pueden crear
    pool_pre_ping=True  # detecta conexiones muertas antes de usarlas
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): 
    pass 

async def get_db() -> AsyncSession: # función para obtener una sesión de la base de datos
    async with AsyncSessionLocal() as session: # crea una sesión de la base de datos
        yield session # retorna la sesión de la base de datos