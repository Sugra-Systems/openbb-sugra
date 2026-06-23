"""Sugra Equity Losers Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_performance import (
    EquityPerformanceData,
    EquityPerformanceQueryParams,
)


class SugraEquityLosersQueryParams(EquityPerformanceQueryParams):
    """Sugra Equity Losers Query Parameters."""


class SugraEquityLosersData(EquityPerformanceData):
    """Sugra Equity Losers Data."""


class SugraEquityLosersFetcher(Fetcher[SugraEquityLosersQueryParams, list[SugraEquityLosersData]]):
    """Fetch the day's top-losing equities from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquityLosersQueryParams:
        """Transform the query parameters."""
        return SugraEquityLosersQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityLosersQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw losers records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models._screener_base import fetch_predefined

        return await fetch_predefined("day_losers", credentials)

    @staticmethod
    def transform_data(
        query: SugraEquityLosersQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityLosersData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.models._screener_base import sort_records

        if not data:
            raise EmptyDataError("No losers data returned.")
        # Losers sort ascending (most negative first) by default.
        sort = "asc" if query.sort == "desc" else "desc"
        return [SugraEquityLosersData.model_validate(d) for d in sort_records(data, sort)]
