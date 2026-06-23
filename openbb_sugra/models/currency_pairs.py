"""Sugra Currency Pairs Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.currency_pairs import (
    CurrencyPairsData,
    CurrencyPairsQueryParams,
)
from pydantic import Field


class SugraCurrencyPairsQueryParams(CurrencyPairsQueryParams):
    """Sugra Currency Pairs Query Parameters."""


class SugraCurrencyPairsData(CurrencyPairsData):
    """Sugra Currency Pairs Data."""

    base_currency: str | None = Field(
        default=None, description="Base currency of the pair (ECB reference base)."
    )
    quote_currency: str | None = Field(default=None, description="Quote currency of the pair.")


class SugraCurrencyPairsFetcher(
    Fetcher[SugraCurrencyPairsQueryParams, list[SugraCurrencyPairsData]]
):
    """List the available Sugra forex currency pairs."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCurrencyPairsQueryParams:
        """Transform the query parameters."""
        return SugraCurrencyPairsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCurrencyPairsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the available currency list from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/forex/currencies", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraCurrencyPairsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraCurrencyPairsData]:
        """Build pair rows (base -> each currency) and validate."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        currencies = (data or {}).get("currencies") or []
        base = (data or {}).get("base") or "EUR"
        if not currencies:
            raise EmptyDataError("No currency pairs returned.")

        rows: list[SugraCurrencyPairsData] = []
        for cur in currencies:
            if cur == base:
                continue
            symbol = f"{base}{cur}"
            rows.append(
                SugraCurrencyPairsData(
                    symbol=symbol,
                    name=f"{base}/{cur}",
                    base_currency=base,
                    quote_currency=cur,
                )
            )

        if query.query:
            needle = query.query.upper()
            rows = [r for r in rows if needle in r.symbol or needle in (r.name or "")]
        if not rows:
            raise EmptyDataError("No currency pairs matched the query.")
        return rows
