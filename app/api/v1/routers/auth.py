from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.schemas.auth import RefreshRequest, TokenResponse, UserRegister, UserResponse
from app.schemas.errors import ErrorResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])

_unauth = {401: {"model": ErrorResponse, "description": "Authentication failed"}}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="""
Create a new user account.

The `email` must be unique — if it is already registered, the API returns **409 Conflict**.

The `role` defaults to `read_only` if not provided. Only supply `admin` or `analyst`
when explicitly granting elevated access.

Passwords are stored as **bcrypt hashes** — never in plain text.
    """,
    responses={
        201: {"description": "User registered successfully"},
        409: {"model": ErrorResponse, "description": "Email already registered"},
        422: {
            "model": ErrorResponse,
            "description": "Validation error — invalid email or password too short",
        },
    },
)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    return await UserService(db).create_user(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="""
Authenticate with email and password using the OAuth2 password flow.

On success, returns:
- `access_token` — short-lived JWT (30 min). Use it in the `Authorization: Bearer <token>` header.
- `refresh_token` — long-lived token (7 days). Use it to renew the access token without re-login.

Returns **401** if the credentials are invalid or the user is deactivated.
    """,
    responses={
        200: {"description": "Login successful — tokens returned"},
        401: {"model": ErrorResponse, "description": "Invalid credentials or inactive user"},
    },
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    service = UserService(db)
    user = await service.authenticate(form_data.username, form_data.password)
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="""
Exchange a valid `refresh_token` for a new `access_token`.

The refresh token is **rotated on every call** — the previous token is immediately
invalidated and a new one is returned. Store the new `refresh_token` from the response.

Returns **401** if the token is expired, malformed, or has already been used.
    """,
    responses={
        200: {"description": "Tokens refreshed successfully"},
        401: {"model": ErrorResponse, "description": "Refresh token invalid or expired"},
    },
)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await UserService(db).refresh_tokens(data.refresh_token)
