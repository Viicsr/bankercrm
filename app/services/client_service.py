from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.schemas.common import PaginatedResponse
from sqlalchemy.orm import selectinload

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
    
    async def list_clients(self, page: int = 1, size: int = 20, only_active: bool = True) -> PaginatedResponse[ClientResponse]:
        offset = (page - 1) * size
        query = select(Client)
        if only_active:
            query = query.where(Client.is_active == True)

        # Total count
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Paginated results
        result = await self.db.execute(
            query.order_by(Client.created_at.desc()).offset(offset).limit(size)
        )
        clients = list(result.scalars().all())

        return PaginatedResponse.create(
            items=[ClientResponse.model_validate(c) for c in clients],
            total=total,
            page=page,
            size=size
        )

    async def get_client_with_accounts(self, client_id: int) -> Client | None:
        result = await self.db.execute(
            select(Client)
            .options(selectinload(Client.accounts))
            .where(Client.id == client_id)
        )
        return result.scalar_one_or_none()

    async def update_client(self, client_id: int, data: ClientUpdate) -> Client | None:
        client = await self.get_client(client_id)
        if not client:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)
        await self.db.commit()
        await self.db.refresh(client)
        return client