"""Sugra Equity Quote Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_quote import (
    EquityQuoteData,
    EquityQuoteQueryParams,
)
from pydantic import Field, model_validator


class SugraEquityQuoteQueryParams(EquityQuoteQueryParams):
    """Sugra Equity Quote Query Parameters."""


class SugraEquityQuoteData(EquityQuoteData):
    """Sugra Equity Quote Data."""

    currency: str | None = Field(
        default=None,
        description="Currency the quote is denominated in.",
    )
    market_cap: float | None = Field(
        default=None,
        description="Market capitalization.",
    )
    market_state: str | None = Field(
        default=None,
        description="Trading session state (PRE, REGULAR, POST, CLOSED).",
    )

    @model_validator(mode="before")
    @classmethod
    def _map_fields(cls, values):
        """Map the Sugra price payload onto the standard quote fields."""
        if not isinstance(values, dict):
            return values
        v = dict(values)
        out: dict = {}
        out["symbol"] = v.get("symbol")
        out["name"] = v.get("longName") or v.get("shortName")
        out["asset_type"] = v.get("quoteType")
        out["exchange"] = v.get("exchange")
        out["last_price"] = v.get("regularMarketPrice")
        out["open"] = v.get("regularMarketOpen")
        out["high"] = v.get("regularMarketDayHigh")
        out["low"] = v.get("regularMarketDayLow")
        out["close"] = v.get("regularMarketPrice")
        out["prev_close"] = v.get("regularMarketPreviousClose")
        out["change"] = v.get("regularMarketChange")
        # The upstream returns change percent as a fraction already (e.g. -0.0033 = -0.33%);
        # the standard model treats this column as a normalized percent.
        out["change_percent"] = v.get("regularMarketChangePercent")
        out["volume"] = v.get("regularMarketVolume")
        out["currency"] = v.get("currency")
        out["market_cap"] = v.get("marketCap")
        out["market_state"] = v.get("marketState")
        return {k: val for k, val in out.items() if val is not None}


class SugraEquityQuoteFetcher(Fetcher[SugraEquityQuoteQueryParams, list[SugraEquityQuoteData]]):
    """Fetch the current equity quote from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquityQuoteQueryParams:
        """Transform the query parameters."""
        return SugraEquityQuoteQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityQuoteQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw quote payload(s) from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        import asyncio

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        symbols = [s.strip().upper() for s in query.symbol.split(",") if s.strip()]

        async def fetch_one(sym: str) -> dict | None:
            response = await sugra_get(f"/api/v2/quotes/{sym}/price", api_key)
            payload = envelope_data(response)
            return payload if isinstance(payload, dict) else None

        results = await asyncio.gather(*[fetch_one(s) for s in symbols])
        return [r for r in results if r]

    @staticmethod
    def transform_data(
        query: SugraEquityQuoteQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityQuoteData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No quote data returned for the symbol.")
        return [SugraEquityQuoteData.model_validate(d) for d in data]
