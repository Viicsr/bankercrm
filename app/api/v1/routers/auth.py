from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.schemas.auth import UserRegister, UserResponse, TokenResponse, RefreshRequest
from app.schemas.errors import ErrorResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])

_unauth = {401: {"model": ErrorResponse, "description": "Authentication failed"}}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse, "description": "Email already registered"}},
)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    return await UserService(db).create_user(data)


@router.post("/login", response_model=TokenResponse, responses=_unauth)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    service = UserService(db)
    user = await service.authenticate(form_data.username, form_data.password)
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse, responses=_unauth)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await UserService(db).refresh_tokens(data.refresh_token)