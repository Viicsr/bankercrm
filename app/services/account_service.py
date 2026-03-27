from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.account import Account
from app.models.client import Client
from app.schemas.account import AccountCreate

class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_client_or_raise(self, client_id: int) -> Client: # funcion auxiliar para obtener el cliente o lanzar un error si no existe
        result = await self.db.execute(
            select(Client).where(Client.id == client_id, Client.is_active == True)
        )
        client = result.scalar_one_or_none()
        if not client:
            raise ValueError(f"Client {client_id} not found or inactive")
        return client

    async def create_account(self, client_id: int, data: AccountCreate) -> Account: # funcion para crear una cuenta
        await self._get_client_or_raise(client_id)

        existing = await self.db.execute( # verificar si la cuenta ya existe
            select(Account).where(Account.account_number == data.account_number)
        )
        if existing.scalar_one_or_none(): # si la cuenta ya existe, lanzar un error
            raise ValueError(f"Account number {data.account_number} already exists")

        account = Account( # crear la cuenta
            client_id=client_id,
            account_number=data.account_number,
            account_type=data.account_type,
            balance=data.balance,
        )
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def get_account(self, account_id: int) -> Account | None: # funcion para obtener una cuenta
        result = await self.db.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_accounts_by_client(self, client_id: int) -> list[Account]: # funcion para obtener todas las cuentas de un cliente
        result = await self.db.execute(
            select(Account).where(Account.client_id == client_id)
        )
        return list(result.scalars().all())