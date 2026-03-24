from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.client import Client
from app.schemas.client import ClientCreate

class ClientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_client(self, data: ClientCreate) -> Client:
        existing = await self.db.execute(
            select(Client).where(Client.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Email {data.email} already registered")

        client = Client(name=data.name, email=data.email)
        self.db.add(client)
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def get_client(self, client_id: int) -> Client | None:
        result = await self.db.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none()