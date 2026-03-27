from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.client import ClientCreate, ClientResponse, ClientWithAccountsResponse, ClientUpdate
from app.services.client_service import ClientService
from app.schemas.common import PaginatedResponse
from typing import Annotated

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate, db: AsyncSession = Depends(get_db)):
    service = ClientService(db)
    try:
        return await service.create_client(client_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.get("/", response_model=PaginatedResponse[ClientResponse])
async def list_clients(
    page: Annotated[int, Query(ge=1)] = 1,           # ge=1: mínimo 1
    size: Annotated[int, Query(ge=1, le=100)] = 20,   # le=100: máximo 100
    only_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    if size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size cannot exceed 100"
        )
    service = ClientService(db)
    return await service.list_clients(page=page, size=size, only_active=only_active)


@router.get("/{client_id}/accounts", response_model=ClientWithAccountsResponse)
async def get_client_with_accounts(
    client_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = ClientService(db)
    client = await service.get_client_with_accounts(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    service = ClientService(db)
    client = await service.get_client(client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client

@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    update_data: ClientUpdate,
    db: AsyncSession = Depends(get_db)
):
    service = ClientService(db)
    client = await service.update_client(client_id, update_data)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client