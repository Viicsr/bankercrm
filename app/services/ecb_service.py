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


def _parse_ecb_response(data: dict) -> dict[str, dict]:
    """
    Parsea la respuesta SDMX-JSON del BCE.
    Estructura: data.dataSets[0].series -> {key: {observations: {period: [value]}}}
    """
    try:
        datasets = data["data"]["dataSets"]
        if not datasets:
            return {}

        series_data = datasets[0].get("series", {})
        structure = data["data"]["structure"]

        # El BCE indexa las dimensiones — necesitamos el mapa de posiciones
        dimensions = structure["dimensions"]["series"]
        currency_dim = next(d for d in dimensions if d["id"] == "CURRENCY")
        currency_values = {str(i): v["id"] for i, v in enumerate(currency_dim["values"])}

        result = {}
        for series_key, series_value in series_data.items():
            # La clave es "0:0:0:0:0" — el segundo elemento es la moneda
            currency_idx = series_key.split(":")[1]
            currency = currency_values.get(currency_idx)
            if not currency:
                continue

            observations = series_value.get("observations", {})
            if not observations:
                continue

            # La última observación es la más reciente
            latest_period = max(observations.keys(), key=int)
            value = observations[latest_period][0]

            # Mapa de períodos para obtener la fecha
            time_periods = structure["dimensions"]["observation"][0]["values"]
            period_date = time_periods[int(latest_period)]["id"]

            result[currency] = {
                "rate": Decimal(str(value)).quantize(Decimal("0.0001")),
                "date": period_date,
                "base": "EUR",
            }

        return result

    except (KeyError, IndexError, StopIteration) as e:
        logger.error("Failed to parse ECB response", extra={"error": str(e)})
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

    rates = _parse_ecb_response(response.json())
    logger.info("FX rates fetched", extra={"count": len(rates)})
    return rates
