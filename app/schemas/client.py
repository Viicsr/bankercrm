from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.account import AccountResponse


class ClientCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Client full name.",
        examples=["María García López"],
    )
    email: EmailStr = Field(
        ...,
        description=(
            "Client email address. Used as the unique identifier — "
            "two clients cannot share the same email."
        ),
        examples=["maria.garcia@banco.es"],
    )


class ClientUpdate(BaseModel):
    name: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="Updated client name.",
        examples=["María García"],
    )
    email: EmailStr | None = Field(
        None,
        description="Updated email address. Must not already exist in the system.",
        examples=["m.garcia@banco.es"],
    )
    is_active: bool | None = Field(
        None,
        description=(
            "Client status. Setting to `false` deactivates the client "
            "without deleting any data or linked accounts."
        ),
    )


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Auto-generated unique client ID.", examples=[1])
    name: str = Field(..., examples=["María García López"])
    email: str = Field(..., examples=["maria.garcia@banco.es"])
    is_active: bool = Field(
        ...,
        description="`false` if the client has been deactivated.",
    )
    created_at: datetime = Field(..., description="UTC timestamp of client creation.")


class ClientWithAccountsResponse(ClientResponse):
    accounts: list[AccountResponse] = Field(
        default=[],
        description="All bank accounts linked to this client.",
    )
