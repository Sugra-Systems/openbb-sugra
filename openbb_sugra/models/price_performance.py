"""Sugra Price Performance Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.recent_performance import (
    RecentPerformanceData,
    RecentPerformanceQueryParams,
)


class SugraPricePerformanceQueryParams(RecentPerformanceQueryParams):
    """Sugra Price Performance Query Parameters."""

    __json_schema_extra__ = {"symbol": {"multiple_items_allowed": True}}


class SugraPricePerformanceData(RecentPerformanceData):
    """Sugra Price Performance Data."""


class SugraPricePerformanceFetcher(
    Fetcher[SugraPricePerformanceQueryParams, list[SugraPricePerformanceData]]
):
    """Fetch trailing price performance for an equity from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraPricePerformanceQueryParams:
        """Transform the query parameters."""
        return SugraPricePerformanceQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraPricePerformanceQueryParams,
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
        query: SugraPricePerformanceQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraPricePerformanceData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No price performance returned for the symbol.")
        return [SugraPricePerformanceData.model_validate(d) for d in data]
