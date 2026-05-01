from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.account import AccountCreate, AccountResponse
from app.schemas.errors import ErrorResponse
from app.services.account_service import AccountService
from app.services.client_service import ClientService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post(
    "/",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse, "description": "Client not found"},
        409: {"model": ErrorResponse, "description": "Account already exists"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
async def create_account(
    client_id: int,
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
):
    service = AccountService(db=db, client_service=ClientService(db=db))
    return await service.create_account(client_id, account_data)


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Account not found"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
    },
)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AccountService(db=db, client_service=ClientService(db=db))
    return await service.get_account(account_id)
