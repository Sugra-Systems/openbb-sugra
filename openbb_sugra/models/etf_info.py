"""Sugra ETF Info Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.etf_info import (
    EtfInfoData,
    EtfInfoQueryParams,
)
from pydantic import Field


class SugraEtfInfoQueryParams(EtfInfoQueryParams):
    """Sugra ETF Info Query Parameters."""


class SugraEtfInfoData(EtfInfoData):
    """Sugra ETF Info Data."""

    category: str | None = Field(default=None, description="Fund category classification.")
    expense_ratio_pct: float | None = Field(
        default=None, description="Net expense ratio, as a percent."
    )
    nav: float | None = Field(default=None, description="Net asset value per share.")
    aum_usd: float | None = Field(default=None, description="Assets under management, in USD.")
    yield_dividend_pct: float | None = Field(
        default=None, description="Trailing dividend yield, as a percent."
    )


class SugraEtfInfoFetcher(Fetcher[SugraEtfInfoQueryParams, list[SugraEtfInfoData]]):
    """Fetch ETF profile/snapshot info from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEtfInfoQueryParams:
        """Transform the query parameters."""
        return SugraEtfInfoQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEtfInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw ETF snapshot from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v1/etf/{query.symbol.upper()}/snapshot", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraEtfInfoQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraEtfInfoData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data or not data.get("symbol"):
            raise EmptyDataError("No ETF info returned for the symbol.")
        row = {
            "symbol": data.get("symbol"),
            "name": data.get("name"),
            "inception_date": data.get("inception_date"),
            "category": data.get("category"),
            "expense_ratio_pct": data.get("expense_ratio_pct"),
            "nav": data.get("nav"),
            "aum_usd": data.get("aum_usd"),
            "yield_dividend_pct": data.get("yield_dividend_pct"),
        }
        return [SugraEtfInfoData.model_validate(row)]
