import logging
from decimal import Decimal

import httpx

from app.core.exceptions import AppBaseException

logger = logging.getLogger(__name__)

ECB_BASE_URL = "https://data-api.ecb.europa.eu/service/data/EXR"

# Monedas soportadas — las más relevantes para un CRM bancario
SUPPORTED_CURRENCIES = ["USD", "GBP", "JPY", "CHF", "CNY", "CAD", "AUD", "SEK", "NOK"]


class ECBServiceError(AppBaseException):
    status_code = 502  # Bad Gateway — el servicio externo falló
    detail = "ECB API unavailable"


def _dimension_value_ids(dimensions: list[dict], dimension_id: str) -> list[str]:
    for dimension in dimensions:
        if dimension.get("id") == dimension_id:
            return [value["id"] for value in dimension.get("values", [])]
    return []


def _parse_ecb_response(data: dict, requested_currencies: list[str]) -> dict[str, dict]:
    """
    Parsea la respuesta SDMX-JSON del BCE (format=jsondata).
    Con detail=dataonly las observaciones usan índices; las fechas y monedas
    se resuelven desde structure.dimensions.
    """
    try:
        datasets = data.get("dataSets")
        if datasets is None:
            datasets = data.get("data", {}).get("dataSets", [])
        if not datasets:
            return {}

        series_data = datasets[0].get("series", {})
        if not series_data:
            return {}

        structure = data.get("structure", {})
        dimensions = structure.get("dimensions", {})
        currency_codes = _dimension_value_ids(dimensions.get("series", []), "CURRENCY")
        time_periods = _dimension_value_ids(dimensions.get("observation", []), "TIME_PERIOD")
        requested = set(requested_currencies)

        result = {}
        for series_key, series_value in series_data.items():
            currency_idx = int(series_key.split(":")[1])
            if currency_idx >= len(currency_codes):
                continue
            currency = currency_codes[currency_idx]
            if requested and currency not in requested:
                continue

            observations = series_value.get("observations", {})
            if not observations:
                continue

            latest_period_key = max(observations.keys(), key=int)
            value = observations[latest_period_key][0]
            period_idx = int(latest_period_key)
            rate_date = (
                time_periods[period_idx] if period_idx < len(time_periods) else latest_period_key
            )

            result[currency] = {
                "rate": Decimal(str(value)).quantize(Decimal("0.0001")),
                "date": rate_date,
                "base": "EUR",
            }

        return result

    except (KeyError, IndexError, ValueError) as e:
        logger.error(
            "Failed to parse ECB response", extra={"error": str(e), "type": type(e).__name__}
        )
        return {}


async def fetch_fx_rates(currencies: list[str] | None = None) -> dict[str, dict]:
    """Obtiene tipos de cambio del BCE para las monedas especificadas."""
    target_currencies = currencies or SUPPORTED_CURRENCIES
    currency_key = "+".join(target_currencies)
    url = f"{ECB_BASE_URL}/D.{currency_key}.EUR.SP00.A"

    params = {
        "lastNObservations": 1,
        "format": "jsondata",
        "detail": "dataonly",
    }

    logger.info("Fetching FX rates from ECB", extra={"currencies": target_currencies})

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
    except httpx.TimeoutException:
        logger.error("ECB API timeout")
        raise ECBServiceError("ECB API timeout — rates unavailable") from None
    except httpx.HTTPStatusError as e:
        logger.error("ECB API HTTP error", extra={"status": e.response.status_code})
        raise ECBServiceError(f"ECB API returned {e.response.status_code}") from e
    except httpx.RequestError as e:
        logger.error("ECB API connection error", extra={"error": str(e)})
        raise ECBServiceError("Cannot connect to ECB API") from e

    rates = _parse_ecb_response(response.json(), target_currencies)
    logger.info("FX rates fetched", extra={"count": len(rates)})
    return rates
