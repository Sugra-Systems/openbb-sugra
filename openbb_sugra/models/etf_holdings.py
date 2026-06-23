"""Sugra ETF Holdings Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.etf_holdings import (
    EtfHoldingsData,
    EtfHoldingsQueryParams,
)
from pydantic import Field


class SugraEtfHoldingsQueryParams(EtfHoldingsQueryParams):
    """Sugra ETF Holdings Query Parameters."""


class SugraEtfHoldingsData(EtfHoldingsData):
    """Sugra ETF Holdings Data."""

    cusip: str | None = Field(default=None, description="CUSIP of the holding.")
    isin: str | None = Field(default=None, description="ISIN of the holding.")
    lei: str | None = Field(default=None, description="Legal Entity Identifier of the holding.")
    value_usd: float | None = Field(
        default=None,
        alias="val_usd",
        description="Market value of the position, in USD.",
    )
    weight: float | None = Field(
        default=None,
        alias="pct_val",
        description="Weight of the holding as a percent of net assets.",
    )
    balance: float | None = Field(default=None, description="Number of shares/units held.")
    asset_category: str | None = Field(
        default=None, alias="asset_cat", description="Asset category code."
    )
    country: str | None = Field(default=None, description="Country of the holding.")
    currency: str | None = Field(default=None, description="Currency of the holding.")


class SugraEtfHoldingsFetcher(Fetcher[SugraEtfHoldingsQueryParams, list[SugraEtfHoldingsData]]):
    """Fetch ETF holdings (SEC N-PORT) from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEtfHoldingsQueryParams:
        """Transform the query parameters."""
        return SugraEtfHoldingsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEtfHoldingsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw holdings from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v1/etf/{query.symbol.upper()}/holdings/sec", api_key)
        payload = envelope_data(response)
        holdings = payload.get("holdings", []) if isinstance(payload, dict) else []
        return holdings or []

    @staticmethod
    def transform_data(
        query: SugraEtfHoldingsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEtfHoldingsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No ETF holdings returned for the symbol.")
        return [SugraEtfHoldingsData.model_validate(d) for d in data]
