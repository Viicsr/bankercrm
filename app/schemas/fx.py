from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FXRate(BaseModel):
    currency: str
    rate: Decimal
    date: str
    base: str = "EUR"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"currency": "USD", "rate": "1.0823", "date": "2026-05-28", "base": "EUR"}
        }
    )


class FXRatesResponse(BaseModel):
    rates: list[FXRate]
    source: str = "European Central Bank"
    description: str = "Daily foreign exchange reference rates against EUR"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rates": [
                    {"currency": "GBP", "rate": "0.8521", "date": "2026-05-28", "base": "EUR"},
                    {"currency": "JPY", "rate": "163.45", "date": "2026-05-28", "base": "EUR"},
                    {"currency": "USD", "rate": "1.0823", "date": "2026-05-28", "base": "EUR"},
                ],
                "source": "European Central Bank",
                "description": "Daily foreign exchange reference rates against EUR",
            }
        }
    )
