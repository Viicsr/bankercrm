from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister
from app.core.security import hash_password, verify_password
from app.core.exceptions import AlreadyExistsError

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        return result.scalar_one_or_none()

    async def create_user(self, data: UserRegister) -> User:
        if await self.get_by_email(data.email):
            raise AlreadyExistsError(entity="User", field="email",value=data.email)
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.get_by_email(email)
        # Mensaje idéntico para ambos casos — no filtra información
        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user