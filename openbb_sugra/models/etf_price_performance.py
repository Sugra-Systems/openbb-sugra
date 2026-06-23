"""Sugra ETF Price Performance Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.recent_performance import (
    RecentPerformanceData,
    RecentPerformanceQueryParams,
)


class SugraEtfPricePerformanceQueryParams(RecentPerformanceQueryParams):
    """Sugra ETF Price Performance Query Parameters."""

    __json_schema_extra__ = {"symbol": {"multiple_items_allowed": True}}


class SugraEtfPricePerformanceData(RecentPerformanceData):
    """Sugra ETF Price Performance Data."""


class SugraEtfPricePerformanceFetcher(
    Fetcher[
        SugraEtfPricePerformanceQueryParams,
        list[SugraEtfPricePerformanceData],
    ]
):
    """Fetch trailing price performance for an ETF from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraEtfPricePerformanceQueryParams:
        """Transform the query parameters."""
        return SugraEtfPricePerformanceQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEtfPricePerformanceQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw recent-performance rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models._recent_performance_base import (
            fetch_recent_performance,
        )

        return await fetch_recent_performance(query.symbol, credentials)

    @staticmethod
    def transform_data(
        query: SugraEtfPricePerformanceQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEtfPricePerformanceData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No ETF price performance returned for the symbol.")
        return [SugraEtfPricePerformanceData.model_validate(d) for d in data]
