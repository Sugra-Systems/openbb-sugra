"""Sugra Equity Most Active Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_performance import (
    EquityPerformanceData,
    EquityPerformanceQueryParams,
)


class SugraEquityActiveQueryParams(EquityPerformanceQueryParams):
    """Sugra Equity Active Query Parameters."""


class SugraEquityActiveData(EquityPerformanceData):
    """Sugra Equity Active Data."""


class SugraEquityActiveFetcher(Fetcher[SugraEquityActiveQueryParams, list[SugraEquityActiveData]]):
    """Fetch the most-active equities from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquityActiveQueryParams:
        """Transform the query parameters."""
        return SugraEquityActiveQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityActiveQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw most-active records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models._screener_base import fetch_predefined

        return await fetch_predefined("MOST_ACTIVES", credentials)

    @staticmethod
    def transform_data(
        query: SugraEquityActiveQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityActiveData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.models._screener_base import sort_records

        if not data:
            raise EmptyDataError("No most-active data returned.")
        return [SugraEquityActiveData.model_validate(d) for d in sort_records(data, query.sort)]
