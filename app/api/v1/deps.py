import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.services.user_service import UserService
from app.core.exceptions import UnauthorizedError, ForbiddenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedError("Could not validate credentials")
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired")
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise UnauthorizedError("Could not validate credentials")

    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise UnauthorizedError("Could not validate credentials")
    return user


def require_roles(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(
                f"Access denied. Required roles: {[r.value for r in roles]}"
            )
        return current_user
    return checker