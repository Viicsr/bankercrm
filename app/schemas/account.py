from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.account import AccountType


class AccountCreate(BaseModel):
    account_number: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="Unique account number. Stored in uppercase. Alphanumeric characters only.",
        examples=["ES12-0049-0001"],
    )
    account_type: AccountType = Field(
        ...,
        description="Account type. Must be one of the values defined in the `AccountType` enum.",
        examples=["checking"],
    )
    balance: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description=(
            "Initial balance in EUR. Must be zero or positive. Cannot be negative at creation time."
        ),
        examples=[Decimal("0.00")],
    )

    @field_validator("balance")
    @classmethod
    def balance_must_be_non_negative(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00"):
            raise ValueError("Balance cannot be negative")
        return v

    @field_validator("account_number")
    @classmethod
    def account_number_format(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Account number cannot be empty")
        return v.upper().strip()


class AccountUpdate(BaseModel):
    is_active: bool | None = Field(
        None,
        description=(
            "Account status. Setting to `false` deactivates the account without deleting any data."
        ),
    )
    balance: Decimal | None = Field(
        None,
        ge=0,
        description="Updated balance in EUR. Must be zero or positive.",
        examples=[Decimal("1500.00")],
    )


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Auto-generated unique account ID.", examples=[1])
    client_id: int = Field(
        ...,
        description="ID of the client this account belongs to.",
        examples=[42],
    )
    account_number: str = Field(
        ...,
        description="Unique account number, stored in uppercase.",
        examples=["ES12-0049-0001"],
    )
    account_type: AccountType = Field(
        ...,
        description="Account type.",
        examples=["checking"],
    )
    balance: Decimal = Field(
        ...,
        description="Current balance in EUR.",
        examples=[Decimal("2500.00")],
    )
    is_active: bool = Field(
        ...,
        description="`false` if the account has been deactivated.",
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp of account creation.",
    )
