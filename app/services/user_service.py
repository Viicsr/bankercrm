import logging

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import TokenResponse, UserRegister

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        logger.info("Getting user by email")
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        logger.info("Getting user by id", extra={"user_id": user_id})
        result = await self.db.execute(select(User).where(User.id == user_id, User.is_active))
        return result.scalar_one_or_none()

    async def create_user(self, data: UserRegister) -> User:
        logger.info("Creating user", extra={"email": data.email})
        if await self.get_by_email(data.email):
            raise ConflictError(f"Email {data.email} already registered")
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info("User created", extra={"user_id": user.id, "email": user.email})
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        logger.info("Authentication attempt")
        user = await self.get_by_email(email)
        # Mensaje idéntico para ambos casos — no filtra información
        if not user or not user.is_active or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        return user

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise UnauthorizedError("Invalid token type")
            user_id = int(payload["sub"])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Refresh token expired, please login again") from None
        except (jwt.InvalidTokenError, KeyError, ValueError):
            raise UnauthorizedError("Invalid refresh token") from None

        user = await self.get_by_id(user_id)
        if not user:
            raise UnauthorizedError("Invalid refresh token")

        return TokenResponse(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id),
        )
