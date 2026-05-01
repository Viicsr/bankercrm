import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.account import Account
from app.models.client import Client
from app.schemas.account import AccountCreate
from app.services.client_service import ClientService

logger = logging.getLogger(__name__)


class AccountService:
    def __init__(self, db: AsyncSession, client_service: ClientService):
        self.db = db
        self.client_service = client_service

    async def _get_client_or_raise(
        self, client_id: int
    ) -> Client:  # funcion auxiliar para obtener el cliente o lanzar un error si no existe
        client = await self.client_service.get_client(client_id)  # Delegado en client service
        if not client or not client.is_active:
            raise NotFoundError(entity="client", entity_id=client_id)
        return client

    async def create_account(
        self, client_id: int, data: AccountCreate
    ) -> Account:  # funcion para crear una cuenta
        await self.client_service.get_client(client_id)

        existing = await self.db.execute(  # verificar si la cuenta ya existe
            select(Account).where(Account.account_number == data.account_number)
        )
        if existing.scalar_one_or_none():  # si la cuenta ya existe, lanzar un error
            raise ConflictError(f"Account number {data.account_number} already exists")

        account = Account(  # crear la cuenta
            client_id=client_id,
            account_number=data.account_number,
            account_type=data.account_type,
            balance=data.balance,
        )
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def get_account(self, account_id: int) -> Account:
        logger.info("Getting account", extra={"account_id": account_id})
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise NotFoundError("Account", account_id)
        return account

    async def get_accounts_by_client(
        self, client_id: int
    ) -> list[Account]:  # funcion para obtener todas las cuentas de un cliente
        logger.info("Getting accounts by client", extra={"client_id": client_id})
        result = await self.db.execute(select(Account).where(Account.client_id == client_id))
        accounts = list(result.scalars().all())
        logger.info("Accounts found", extra={"client_id": client_id, "count": len(accounts)})
        return accounts
