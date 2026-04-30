from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.account import AccountType


class AccountCreate(BaseModel):
    account_number: str
    account_type: AccountType
    balance: Decimal = Decimal("0.00")

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
    is_active: bool | None = None
    balance: Decimal | None = None

class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    account_number: str
    account_type: AccountType
    balance: Decimal
    is_active: bool
    created_at: datetime
