from decimal import Decimal

from pydantic import BaseModel


class FXRate(BaseModel):
    currency: str
    rate: Decimal
    date: str
    base: str = "EUR"


class FXRatesResponse(BaseModel):
    rates: list[FXRate]
    source: str = "European Central Bank"
    description: str = "Daily foreign exchange reference rates against EUR"
