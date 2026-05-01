from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.client import (
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    ClientWithAccountsResponse,
)
from app.schemas.common import PaginatedResponse
from app.schemas.errors import ErrorResponse
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["Clients"])

_auth_responses = {
    401: {"model": ErrorResponse, "description": "Not authenticated"},
    403: {"model": ErrorResponse, "description": "Insufficient permissions"},
}


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
        **_auth_responses,
    },
)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
):
    service = ClientService(db)
    return await service.create_client(client_data)


@router.get(
    "/",
    response_model=PaginatedResponse[ClientResponse],
    responses=_auth_responses,
)
async def list_clients(
    page: Annotated[int, Query(ge=1)] = 1,  # ge=1: mínimo 1
    size: Annotated[int, Query(ge=1, le=100)] = 20,  # le=100: máximo 100
    only_active: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # cualquier rol autenticado
):
    service = ClientService(db)
    return await service.list_clients(page=page, size=size, only_active=only_active)


@router.get(
    "/{client_id}/accounts",
    response_model=ClientWithAccountsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Client not found"},
        **_auth_responses,
    },
)
async def get_client_with_accounts(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClientService(db)
    return await service.get_client_with_accounts(client_id)


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Client not found"},
        **_auth_responses,
    },
)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClientService(db)
    return await service.get_client(client_id)


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Client not found"},
        409: {"model": ErrorResponse, "description": "Email already registered"},
        **_auth_responses,
    },
)
async def update_client(
    client_id: int,
    update_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
):
    service = ClientService(db)
    return await service.update_client(client_id, update_data)
