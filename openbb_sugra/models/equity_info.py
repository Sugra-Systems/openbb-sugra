"""Sugra Equity Info Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_info import (
    EquityInfoData,
    EquityInfoQueryParams,
)
from pydantic import Field, model_validator


class SugraEquityInfoQueryParams(EquityInfoQueryParams):
    """Sugra Equity Info Query Parameters."""


class SugraEquityInfoData(EquityInfoData):
    """Sugra Equity Info Data."""

    market_cap: float | None = Field(default=None, description="Market capitalization.")
    beta: float | None = Field(default=None, description="Beta of the stock.")
    dividend_yield: float | None = Field(
        default=None, description="Trailing dividend yield (normalized)."
    )

    @model_validator(mode="before")
    @classmethod
    def _map_fields(cls, values):
        """Map the Sugra info payload onto the standard info fields."""
        if not isinstance(values, dict):
            return values
        v = dict(values)
        out: dict = {}
        out["symbol"] = v.get("symbol")
        out["name"] = v.get("longName") or v.get("shortName")
        out["stock_exchange"] = v.get("exchange") or v.get("fullExchangeName")
        out["company_url"] = v.get("website")
        out["business_phone_no"] = v.get("phone")
        out["hq_address1"] = v.get("address1")
        out["hq_address_city"] = v.get("city")
        out["hq_state"] = v.get("state")
        out["hq_address_postal_code"] = v.get("zip")
        out["hq_country"] = v.get("country")
        out["sector"] = v.get("sectorDisp") or v.get("sector")
        out["industry_category"] = v.get("industryDisp") or v.get("industry")
        out["long_description"] = v.get("longBusinessSummary")
        out["employees"] = v.get("fullTimeEmployees")
        out["market_cap"] = v.get("marketCap")
        out["beta"] = v.get("beta")
        out["dividend_yield"] = v.get("dividendYield")
        return {k: val for k, val in out.items() if val is not None}


class SugraEquityInfoFetcher(Fetcher[SugraEquityInfoQueryParams, list[SugraEquityInfoData]]):
    """Fetch detailed company info from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquityInfoQueryParams:
        """Transform the query parameters."""
        return SugraEquityInfoQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw info payload(s) from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        import asyncio

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        symbols = [s.strip().upper() for s in query.symbol.split(",") if s.strip()]

        async def fetch_one(sym: str) -> dict | None:
            response = await sugra_get(f"/api/v2/quotes/{sym}/info", api_key)
            payload = envelope_data(response)
            if isinstance(payload, dict):
                payload.setdefault("symbol", sym)
                return payload
            return None

        results = await asyncio.gather(*[fetch_one(s) for s in symbols])
        return [r for r in results if r]

    @staticmethod
    def transform_data(
        query: SugraEquityInfoQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityInfoData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No company info returned for the symbol.")
        return [SugraEquityInfoData.model_validate(d) for d in data]
