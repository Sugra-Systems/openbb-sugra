"""Sugra Equity Ownership Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_ownership import (
    EquityOwnershipData,
    EquityOwnershipQueryParams,
)
from pydantic import Field, model_validator


class SugraEquityOwnershipQueryParams(EquityOwnershipQueryParams):
    """Sugra Equity Ownership Query Parameters."""


class SugraEquityOwnershipData(EquityOwnershipData):
    """Sugra Equity Ownership Data."""

    shares: int | None = Field(default=None, description="Shares held.")
    market_value: float | None = Field(default=None, description="Market value of the position.")
    weight: float | None = Field(
        default=None, description="Percent of the company held by this investor."
    )
    change: float | None = Field(
        default=None, description="Percent change in the position since the prior period."
    )
    holder_type: str | None = Field(
        default=None, description="Holder category (institutional or fund)."
    )

    @model_validator(mode="before")
    @classmethod
    def _map_fields(cls, values):
        """Map a Sugra holders row onto the standard ownership fields."""
        if not isinstance(values, dict):
            return values
        v = dict(values)
        reported = v.get("date_reported")
        date_only: str | None = None
        if isinstance(reported, str) and reported:
            date_only = reported[:10]
        return {
            "investor_name": v.get("holder"),
            "symbol": v.get("symbol"),
            "date": date_only,
            "filing_date": date_only,
            "shares": v.get("shares"),
            "market_value": v.get("value"),
            "weight": v.get("pct_held"),
            "change": v.get("pct_change"),
            "holder_type": v.get("holder_type"),
        }


class SugraEquityOwnershipFetcher(
    Fetcher[SugraEquityOwnershipQueryParams, list[SugraEquityOwnershipData]]
):
    """Fetch institutional/fund ownership from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquityOwnershipQueryParams:
        """Transform the query parameters."""
        return SugraEquityOwnershipQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityOwnershipQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw holders rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        symbol = query.symbol.upper()
        response = await sugra_get(f"/api/v2/quotes/{symbol}/holders/summary", api_key)
        payload = envelope_data(response)
        if not isinstance(payload, dict):
            return []
        rows: list[dict] = []
        for holder in payload.get("top_institutional", []) or []:
            if isinstance(holder, dict) and holder.get("holder"):
                rows.append({**holder, "symbol": symbol, "holder_type": "institutional"})
        for holder in payload.get("top_funds", []) or []:
            if isinstance(holder, dict) and holder.get("holder"):
                rows.append({**holder, "symbol": symbol, "holder_type": "fund"})
        return rows

    @staticmethod
    def transform_data(
        query: SugraEquityOwnershipQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityOwnershipData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No ownership data returned for the symbol.")
        return [SugraEquityOwnershipData.model_validate(d) for d in data]
