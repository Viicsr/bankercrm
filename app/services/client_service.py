import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)


class ClientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_client(self, data: ClientCreate) -> Client:
        logger.info("Creating client", extra={"email": data.email})
        existing = await self.db.execute(select(Client).where(Client.email == data.email))
        if existing.scalar_one_or_none():
            raise ConflictError(f"Email {data.email} already registered")

        client = Client(name=data.name, email=data.email)
        self.db.add(client)
        await self.db.commit()
        await self.db.refresh(client)
        logger.info("Client created", extra={"client_id": client.id, "email": client.email})
        return client

    async def get_client(self, client_id: int) -> Client:
        result = await self.db.execute(select(Client).where(Client.id == client_id))
        client = result.scalar_one_or_none()
        if not client:
            raise NotFoundError("Client", client_id)
        return client

    async def list_clients(
        self, page: int = 1, size: int = 20, only_active: bool = True
    ) -> PaginatedResponse[ClientResponse]:
        logger.debug(
            "Listing clients", extra={"page": page, "size": size, "only_active": only_active}
        )
        offset = (page - 1) * size
        query = select(Client)
        if only_active:
            query = query.where(Client.is_active)

        # Total count
        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
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
            size=size,
        )

    async def get_client_with_accounts(self, client_id: int) -> Client:
        logger.info("Getting client with accounts", extra={"client_id": client_id})
        result = await self.db.execute(
            select(Client).options(selectinload(Client.accounts)).where(Client.id == client_id)
        )
        client = result.scalar_one_or_none()
        if not client:
            raise NotFoundError("Client", client_id)
        logger.info(
            "Client with accounts found", extra={"client_id": client.id, "email": client.email}
        )
        return client

    async def update_client(self, client_id: int, data: ClientUpdate) -> Client:
        logger.info(
            "Updating client",
            extra={
                "client_id": client_id,
                "fields": list(data.model_dump(exclude_unset=True).keys()),
            },
        )
        client = await self.get_client(client_id)
        update_data = data.model_dump(exclude_unset=True)

        if "email" in update_data:
            existing = await self.db.execute(
                select(Client).where(
                    Client.email == update_data["email"],
                    Client.id != client_id,
                )
            )
            if existing.scalar_one_or_none():
                raise ConflictError(f"Email {update_data['email']} already in use")

        for field, value in update_data.items():
            setattr(client, field, value)
        await self.db.commit()
        await self.db.refresh(client)
        logger.info("Client updated", extra={"client_id": client.id, "email": client.email})
        return client
