"""Sugra Share Statistics Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.share_statistics import (
    ShareStatisticsData,
    ShareStatisticsQueryParams,
)
from pydantic import Field


def _latest(series: Any) -> dict | None:
    """Return the most recent {end, val, ...} fact from a series list."""
    if isinstance(series, list) and series and isinstance(series[0], dict):
        return series[0]
    return None


class SugraShareStatisticsQueryParams(ShareStatisticsQueryParams):
    """Sugra Share Statistics Query Parameters."""


class SugraShareStatisticsData(ShareStatisticsData):
    """Sugra Share Statistics Data."""

    shares_issued: float | None = Field(default=None, description="Total shares issued.")
    shares_authorized: float | None = Field(default=None, description="Total shares authorized.")
    weighted_avg_shares_basic: float | None = Field(
        default=None, description="Weighted average basic shares outstanding."
    )
    weighted_avg_shares_diluted: float | None = Field(
        default=None, description="Weighted average diluted shares outstanding."
    )
    dividends_per_share: float | None = Field(
        default=None, description="Dividends declared per share."
    )
    stock_based_compensation: float | None = Field(
        default=None, description="Stock-based compensation expense."
    )


class SugraShareStatisticsFetcher(
    Fetcher[SugraShareStatisticsQueryParams, list[SugraShareStatisticsData]]
):
    """Fetch share statistics from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraShareStatisticsQueryParams:
        """Transform the query parameters."""
        return SugraShareStatisticsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraShareStatisticsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw shares-detail snapshot from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(
            f"/api/v1/fundamentals/{query.symbol.upper()}/shares-detail", api_key
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraShareStatisticsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraShareStatisticsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        outstanding = _latest((data or {}).get("shares_outstanding"))
        if not outstanding or outstanding.get("val") is None:
            raise EmptyDataError("No share statistics returned for the symbol.")

        row: dict[str, Any] = {
            "symbol": query.symbol.upper(),
            "date": outstanding.get("end"),
            "outstanding_shares": outstanding.get("val"),
        }
        for std_field, series_key in (
            ("shares_issued", "shares_issued"),
            ("shares_authorized", "shares_authorized"),
            ("weighted_avg_shares_basic", "weighted_avg_shares_basic"),
            ("weighted_avg_shares_diluted", "weighted_avg_shares_diluted"),
            ("dividends_per_share", "dividends_per_share"),
            ("stock_based_compensation", "stock_based_compensation"),
        ):
            fact = _latest(data.get(series_key))
            if fact and fact.get("val") is not None:
                row[std_field] = fact["val"]
        return [SugraShareStatisticsData.model_validate(row)]
