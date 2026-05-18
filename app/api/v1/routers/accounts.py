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
    summary="Create account",
    description="""
Create a new bank account linked to an existing client.

Supply the target `client_id` as a query parameter. The client must exist
and be **active** — creating an account for a deactivated client returns **404**.

The `account_number` must be unique across the entire system.
If it already exists, the API returns **409 Conflict**.

Requires `admin` or `analyst` role.
    """,
    responses={
        201: {"description": "Account created successfully"},
        404: {"model": ErrorResponse, "description": "Client not found or inactive"},
        409: {"model": ErrorResponse, "description": "Account number already exists"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {
            "model": ErrorResponse,
            "description": "Insufficient permissions — admin or analyst required",
        },
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
    summary="Get account by ID",
    description="""
Return the details of a specific bank account.

Accessible by any authenticated user regardless of role.
Returns **404** if the account does not exist.
    """,
    responses={
        200: {"description": "Account found"},
        404: {"model": ErrorResponse, "description": "Account not found"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
    },
)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AccountService(db=db, client_service=ClientService(db=db))
    return await service.get_account(account_id)
