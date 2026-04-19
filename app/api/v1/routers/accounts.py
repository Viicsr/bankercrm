from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.account import AccountCreate, AccountResponse
from app.services.account_service import AccountService
from app.services.client_service import ClientService
from app.api.v1.deps import get_current_user, require_roles
from app.models.user import User, UserRole

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    client_id: int,
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST))
):
    service = AccountService(db=db,client_service=ClientService(db=db))
    return await service.create_account(client_id, account_data)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, 
    db: AsyncSession = Depends(get_db),    
    current_user: User = Depends(get_current_user)
):
    service = AccountService(db=db,client_service=ClientService(db=db))
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account