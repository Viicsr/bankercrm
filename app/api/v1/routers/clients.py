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
    401: {"model": ErrorResponse, "description": "Authentication required"},
    403: {"model": ErrorResponse, "description": "Insufficient permissions"},
}


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create client",
    description="""
Create a new client in the CRM.

The `email` must be unique — if a client with that email already exists,
the API returns **409 Conflict**.

Requires `admin` or `analyst` role.
    """,
    responses={
        201: {"description": "Client created successfully"},
        409: {"model": ErrorResponse, "description": "Email already registered"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {
            "model": ErrorResponse,
            "description": "Insufficient permissions — admin or analyst required",
        },
        422: {
            "model": ErrorResponse,
            "description": "Validation error — invalid email or name too short",
        },
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
    summary="List clients",
    description="""
Return a paginated list of clients.

Use `only_active=false` to include deactivated clients in the results.
Pagination is controlled by `page` (1-based) and `size` (max 100 per page).

Accessible by any authenticated user regardless of role.
    """,
    responses={
        200: {"description": "Paginated list of clients"},
        **_auth_responses,
    },
)
async def list_clients(
    page: Annotated[int, Query(ge=1, description="Page number (1-based).")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Results per page. Maximum 100.")] = 20,
    only_active: bool = Query(True, description="If `true`, returns only active clients."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClientService(db)
    return await service.list_clients(page=page, size=size, only_active=only_active)


@router.get(
    "/{client_id}/accounts",
    response_model=ClientWithAccountsResponse,
    summary="Get client with accounts",
    description="""
Return a client and all their linked bank accounts.

This endpoint uses a single query with `selectinload` to fetch
the client and all associated accounts efficiently.

Accessible by any authenticated user regardless of role.
    """,
    responses={
        200: {"description": "Client with account list"},
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
    summary="Get client by ID",
    description="""
Return the details of a specific client.

Returns **404** if no client exists with the given ID.

Accessible by any authenticated user regardless of role.
    """,
    responses={
        200: {"description": "Client found"},
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
    summary="Update client",
    description="""
Partially update a client's data.

All fields are optional — only the fields included in the request body are updated.
If `email` is changed, the new value must not already exist in the system.

Setting `is_active` to `false` deactivates the client without deleting any data
or their associated accounts.

Requires `admin` or `analyst` role.
    """,
    responses={
        200: {"description": "Client updated successfully"},
        404: {"model": ErrorResponse, "description": "Client not found"},
        409: {"model": ErrorResponse, "description": "Email already in use by another client"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {
            "model": ErrorResponse,
            "description": "Insufficient permissions — admin or analyst required",
        },
        422: {
            "description": "Validation error — invalid email format or name too short",
        },
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
