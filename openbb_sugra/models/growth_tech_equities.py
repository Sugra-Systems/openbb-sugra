"""Sugra Growth Tech Equities Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_performance import (
    EquityPerformanceData,
    EquityPerformanceQueryParams,
)


class SugraGrowthTechEquitiesQueryParams(EquityPerformanceQueryParams):
    """Sugra Growth Tech Equities Query Parameters."""


class SugraGrowthTechEquitiesData(EquityPerformanceData):
    """Sugra Growth Tech Equities Data."""


class SugraGrowthTechEquitiesFetcher(
    Fetcher[
        SugraGrowthTechEquitiesQueryParams,
        list[SugraGrowthTechEquitiesData],
    ]
):
    """Fetch growth technology equities from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraGrowthTechEquitiesQueryParams:
        """Transform the query parameters."""
        return SugraGrowthTechEquitiesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraGrowthTechEquitiesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw growth-technology records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models._screener_base import fetch_predefined

        return await fetch_predefined("growth_technology_stocks", credentials)

    @staticmethod
    def transform_data(
        query: SugraGrowthTechEquitiesQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraGrowthTechEquitiesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.models._screener_base import sort_records

        if not data:
            raise EmptyDataError("No growth-technology equity data returned.")
        return [
            SugraGrowthTechEquitiesData.model_validate(d) for d in sort_records(data, query.sort)
        ]
