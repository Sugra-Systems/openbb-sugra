"""Sugra Market Snapshots Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.market_snapshots import (
    MarketSnapshotsData,
    MarketSnapshotsQueryParams,
)
from pydantic import model_validator


class SugraMarketSnapshotsQueryParams(MarketSnapshotsQueryParams):
    """Sugra Market Snapshots Query Parameters."""


class SugraMarketSnapshotsData(MarketSnapshotsData):
    """Sugra Market Snapshots Data."""

    @model_validator(mode="before")
    @classmethod
    def _map_fields(cls, values):
        """Map a Sugra market summary row onto the standard snapshot fields."""
        if not isinstance(values, dict):
            return values
        v = dict(values)
        change_pct = v.get("change_pct")
        out = {
            "symbol": v.get("symbol"),
            "name": v.get("short_name"),
            "exchange": v.get("exchange"),
            "close": v.get("price"),
            "change": v.get("change"),
            # The upstream summary returns percent like -1.29 (-1.29%); normalize to a fraction.
            "change_percent": (change_pct / 100.0) if change_pct is not None else None,
        }
        return {k: val for k, val in out.items() if val is not None}


class SugraMarketSnapshotsFetcher(
    Fetcher[SugraMarketSnapshotsQueryParams, list[SugraMarketSnapshotsData]]
):
    """Fetch a market-wide snapshot of major indices from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraMarketSnapshotsQueryParams:
        """Transform the query parameters."""
        return SugraMarketSnapshotsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraMarketSnapshotsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw market summary rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v2/market/summary", api_key)
        payload = envelope_data(response)
        if isinstance(payload, list):
            return [r for r in payload if isinstance(r, dict)]
        return []

    @staticmethod
    def transform_data(
        query: SugraMarketSnapshotsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraMarketSnapshotsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No market snapshot data returned.")
        return [SugraMarketSnapshotsData.model_validate(d) for d in data]
