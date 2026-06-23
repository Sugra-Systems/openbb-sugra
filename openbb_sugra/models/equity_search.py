"""Sugra Equity Search Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_search import (
    EquitySearchData,
    EquitySearchQueryParams,
)
from pydantic import Field, model_validator


class SugraEquitySearchQueryParams(EquitySearchQueryParams):
    """Sugra Equity Search Query Parameters."""


class SugraEquitySearchData(EquitySearchData):
    """Sugra Equity Search Data."""

    exchange: str | None = Field(default=None, description="Exchange the security is listed on.")
    asset_type: str | None = Field(default=None, description="Instrument type (EQUITY, ETF, etc.).")

    @model_validator(mode="before")
    @classmethod
    def _map_fields(cls, values):
        """Map a Sugra search quote onto the standard search fields."""
        if not isinstance(values, dict):
            return values
        v = dict(values)
        return {
            "symbol": v.get("symbol"),
            "name": v.get("long_name") or v.get("short_name"),
            "exchange": v.get("exchange"),
            "asset_type": v.get("type"),
        }


class SugraEquitySearchFetcher(Fetcher[SugraEquitySearchQueryParams, list[SugraEquitySearchData]]):
    """Search tickers via the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquitySearchQueryParams:
        """Transform the query parameters."""
        return SugraEquitySearchQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquitySearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw search quotes from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v2/market/search", api_key, {"q": query.query})
        payload = envelope_data(response)
        quotes = payload.get("quotes", []) if isinstance(payload, dict) else []
        return [q for q in quotes if isinstance(q, dict) and q.get("symbol")]

    @staticmethod
    def transform_data(
        query: SugraEquitySearchQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquitySearchData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No search results returned for the query.")
        return [SugraEquitySearchData.model_validate(d) for d in data]
