from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import hash_password
from app.schemas.account import AccountCreate
from app.schemas.client import ClientCreate, ClientUpdate
from app.services.account_service import AccountService
from app.services.client_service import ClientService
from app.services.user_service import UserService


# helpers
def make_execute_mock(return_value):
    """Devuelve un mock_db.execute que retorna un MagicMock síncrono con scalar_one_or_none."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = return_value
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute = AsyncMock(return_value=mock_result)
    return mock_db


# ── CLIENT SERVICE ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_client_duplicate_raises_conflict():
    mock_db = make_execute_mock(return_value=MagicMock())  # simula cliente existente

    service = ClientService(mock_db)
    with pytest.raises(ConflictError):
        await service.create_client(ClientCreate(name="Test", email="dup@test.com"))


@pytest.mark.asyncio
async def test_get_client_not_found_raises():
    mock_db = make_execute_mock(return_value=None)  # simula no encontrado

    service = ClientService(mock_db)
    with pytest.raises(NotFoundError):
        await service.get_client(99999)


@pytest.mark.asyncio
async def test_update_client_not_found_raises():
    mock_db = AsyncMock(spec=AsyncSession)

    service = ClientService(mock_db)
    with patch.object(service, "get_client", side_effect=NotFoundError("Client", 99999)):
        with pytest.raises(NotFoundError):
            await service.update_client(99999, ClientUpdate(name="New"))


@pytest.mark.asyncio
async def test_list_clients_inactive_included():
    mock_db = AsyncMock(spec=AsyncSession)
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [count_result, items_result]

    service = ClientService(mock_db)
    result = await service.list_clients(page=1, size=10, only_active=False)
    assert result.total == 0


@pytest.mark.asyncio
async def test_get_client_with_accounts_not_found():
    mock_db = make_execute_mock(return_value=None)

    service = ClientService(mock_db)
    with pytest.raises(NotFoundError):
        await service.get_client_with_accounts(99999)


# ── ACCOUNT SERVICE ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_account_duplicate_raises_conflict():
    mock_db = make_execute_mock(return_value=MagicMock())  # cuenta ya existe
    mock_client_service = AsyncMock()
    mock_client_service.get_client.return_value = MagicMock()

    service = AccountService(mock_db, mock_client_service)
    with pytest.raises(ConflictError):
        await service.create_account(
            1, AccountCreate(account_number="ES001", account_type="checking", balance="100")
        )


@pytest.mark.asyncio
async def test_get_account_not_found_raises():
    mock_db = make_execute_mock(return_value=None)

    service = AccountService(mock_db, AsyncMock())
    with pytest.raises(NotFoundError):
        await service.get_account(99999)


@pytest.mark.asyncio
async def test_get_client_or_raise_inactive_client():
    mock_db = AsyncMock(spec=AsyncSession)
    mock_client_service = AsyncMock()
    inactive_client = MagicMock()
    inactive_client.is_active = False
    mock_client_service.get_client.return_value = inactive_client

    service = AccountService(mock_db, mock_client_service)
    with pytest.raises(NotFoundError):
        await service._get_client_or_raise(1)


# ── USER SERVICE ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_user_duplicate_raises_conflict():
    mock_db = AsyncMock(spec=AsyncSession)

    service = UserService(mock_db)
    existing_user = MagicMock()
    with patch.object(service, "get_by_email", return_value=existing_user):
        from app.schemas.auth import UserRegister

        with pytest.raises(ConflictError):
            await service.create_user(UserRegister(email="dup@test.com", password="Pass1234!"))


@pytest.mark.asyncio
async def test_authenticate_wrong_password_raises():
    mock_db = AsyncMock(spec=AsyncSession)
    real_user = MagicMock()
    real_user.is_active = True
    real_user.hashed_password = hash_password("password_correcto")

    service = UserService(mock_db)
    with patch.object(service, "get_by_email", return_value=real_user):
        with pytest.raises(UnauthorizedError):
            await service.authenticate("user@test.com", "wrongpassword")


@pytest.mark.asyncio
async def test_authenticate_inactive_user_raises():
    mock_db = AsyncMock(spec=AsyncSession)
    inactive_user = MagicMock()
    inactive_user.is_active = False
    inactive_user.hashed_password = "irrelevante"

    service = UserService(mock_db)
    with patch.object(service, "get_by_email", return_value=inactive_user):
        with pytest.raises(UnauthorizedError):
            await service.authenticate("inactive@test.com", "Pass1234!")


@pytest.mark.asyncio
async def test_refresh_tokens_expired_raises():
    from datetime import datetime, timedelta

    import jwt as pyjwt

    from app.core.config import settings

    expired_payload = {
        "sub": "1",
        "type": "refresh",
        "exp": datetime.now(UTC) - timedelta(hours=1),
    }
    expired_token = pyjwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")

    service = UserService(AsyncMock(spec=AsyncSession))
    with pytest.raises(UnauthorizedError, match="expired"):
        await service.refresh_tokens(expired_token)


@pytest.mark.asyncio
async def test_refresh_tokens_wrong_type_raises():
    from app.core.security import create_access_token

    access_token = create_access_token(user_id=1, role="admin")

    service = UserService(AsyncMock(spec=AsyncSession))
    with pytest.raises(UnauthorizedError):
        await service.refresh_tokens(access_token)


@pytest.mark.asyncio
async def test_refresh_tokens_user_not_found_raises():
    from app.core.security import create_refresh_token

    token = create_refresh_token(user_id=99999)

    mock_db = AsyncMock(spec=AsyncSession)
    service = UserService(mock_db)
    with patch.object(service, "get_by_id", return_value=None):
        with pytest.raises(UnauthorizedError):
            await service.refresh_tokens(token)
