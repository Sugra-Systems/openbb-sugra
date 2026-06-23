"""Sugra Undervalued Growth Equities Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_performance import (
    EquityPerformanceData,
    EquityPerformanceQueryParams,
)


class SugraUndervaluedGrowthEquitiesQueryParams(EquityPerformanceQueryParams):
    """Sugra Undervalued Growth Equities Query Parameters."""


class SugraUndervaluedGrowthEquitiesData(EquityPerformanceData):
    """Sugra Undervalued Growth Equities Data."""


class SugraUndervaluedGrowthEquitiesFetcher(
    Fetcher[
        SugraUndervaluedGrowthEquitiesQueryParams,
        list[SugraUndervaluedGrowthEquitiesData],
    ]
):
    """Fetch undervalued growth equities from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraUndervaluedGrowthEquitiesQueryParams:
        """Transform the query parameters."""
        return SugraUndervaluedGrowthEquitiesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraUndervaluedGrowthEquitiesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw undervalued-growth records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models._screener_base import fetch_predefined

        return await fetch_predefined("undervalued_growth_stocks", credentials)

    @staticmethod
    def transform_data(
        query: SugraUndervaluedGrowthEquitiesQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraUndervaluedGrowthEquitiesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.models._screener_base import sort_records

        if not data:
            raise EmptyDataError("No undervalued growth data returned.")
        return [
            SugraUndervaluedGrowthEquitiesData.model_validate(d)
            for d in sort_records(data, query.sort)
        ]
