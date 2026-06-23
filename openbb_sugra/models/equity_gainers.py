"""Sugra Equity Gainers Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_performance import (
    EquityPerformanceData,
    EquityPerformanceQueryParams,
)


class SugraEquityGainersQueryParams(EquityPerformanceQueryParams):
    """Sugra Equity Gainers Query Parameters."""


class SugraEquityGainersData(EquityPerformanceData):
    """Sugra Equity Gainers Data."""


class SugraEquityGainersFetcher(
    Fetcher[SugraEquityGainersQueryParams, list[SugraEquityGainersData]]
):
    """Fetch the day's top-gaining equities from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquityGainersQueryParams:
        """Transform the query parameters."""
        return SugraEquityGainersQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityGainersQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw gainers records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models._screener_base import fetch_predefined

        return await fetch_predefined("day_gainers", credentials)

    @staticmethod
    def transform_data(
        query: SugraEquityGainersQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityGainersData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.models._screener_base import sort_records

        if not data:
            raise EmptyDataError("No gainers data returned.")
        return [SugraEquityGainersData.model_validate(d) for d in sort_records(data, query.sort)]
