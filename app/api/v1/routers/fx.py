import logging
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.fx import FXRate, FXRatesResponse
from app.services.account_service import AccountService
from app.services.ecb_service import SUPPORTED_CURRENCIES, fetch_fx_rates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fx", tags=["Foreign Exchange"])


@router.get(
    "/rates",
    response_model=FXRatesResponse,
    summary="Current foreign exchange rates (ECB)",
    description="""
Returns the daily reference exchange rates published by the
European Central Bank. All rates are quoted against EUR (base currency).

Data is fetched in real time from the ECB public API:
`data-api.ecb.europa.eu`

Updated once per business day at approximately 16:00 CET.
    """,
)
async def get_fx_rates(
    currencies: list[str] = Query(
        default=None,
        description=f"Currency codes to query. Available: {', '.join(SUPPORTED_CURRENCIES)}",
        examples=["USD", "GBP"],
    ),
    current_user: User = Depends(get_current_user),
):
    rates_data = await fetch_fx_rates(currencies)
    rates = [
        FXRate(
            currency=currency,
            rate=data["rate"],
            date=data["date"],
            base=data["base"],
        )
        for currency, data in rates_data.items()
    ]
    return FXRatesResponse(rates=sorted(rates, key=lambda r: r.currency))


@router.get(
    "/accounts/{account_id}/convert",
    summary="Convert account balance to other currencies",
    description="""
Retrieves the balance of a specific bank account and converts it
to the selected currencies using live ECB exchange rates.

Combines internal CRM data (account balance) with real-time
external data (ECB exchange rates).
    """,
    responses={
        200: {
            "description": "Balance converted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "account_id": 1,
                        "account_number": "ES1234567890",
                        "balance_eur": 1000.00,
                        "conversions": {
                            "GBP": {"amount": 852.10, "rate": 0.8521, "rate_date": "2026-05-28"},
                            "JPY": {"amount": 163450.00, "rate": 163.45, "rate_date": "2026-05-28"},
                            "USD": {"amount": 1082.30, "rate": 1.0823, "rate_date": "2026-05-28"},
                        },
                        "source": "European Central Bank",
                    }
                }
            },
        },
        404: {"description": "Account not found"},
        502: {"description": "ECB API unavailable"},
    },
)
async def convert_account_balance(
    account_id: int,
    currencies: list[str] = Query(
        default=["USD", "GBP", "JPY"],
        description="Target currency codes for conversion",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await AccountService(db).get_account(account_id)
    balance_eur = account.balance

    rates_data = await fetch_fx_rates(currencies)

    conversions = {}
    for currency, rate_info in rates_data.items():
        converted = (balance_eur * rate_info["rate"]).quantize(Decimal("0.01"))
        conversions[currency] = {
            "amount": float(converted),
            "rate": float(rate_info["rate"]),
            "rate_date": rate_info["date"],
        }

    return {
        "account_id": account_id,
        "account_number": account.account_number,
        "balance_eur": float(balance_eur),
        "conversions": conversions,
        "source": "European Central Bank",
    }
