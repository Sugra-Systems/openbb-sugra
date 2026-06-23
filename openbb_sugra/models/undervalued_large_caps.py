"""Sugra Undervalued Large Caps Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_performance import (
    EquityPerformanceData,
    EquityPerformanceQueryParams,
)


class SugraUndervaluedLargeCapsQueryParams(EquityPerformanceQueryParams):
    """Sugra Undervalued Large Caps Query Parameters."""


class SugraUndervaluedLargeCapsData(EquityPerformanceData):
    """Sugra Undervalued Large Caps Data."""


class SugraUndervaluedLargeCapsFetcher(
    Fetcher[
        SugraUndervaluedLargeCapsQueryParams,
        list[SugraUndervaluedLargeCapsData],
    ]
):
    """Fetch undervalued large-cap equities from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraUndervaluedLargeCapsQueryParams:
        """Transform the query parameters."""
        return SugraUndervaluedLargeCapsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraUndervaluedLargeCapsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw undervalued large-cap records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models._screener_base import fetch_predefined

        return await fetch_predefined("undervalued_large_caps", credentials)

    @staticmethod
    def transform_data(
        query: SugraUndervaluedLargeCapsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraUndervaluedLargeCapsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.models._screener_base import sort_records

        if not data:
            raise EmptyDataError("No undervalued large-cap data returned.")
        return [
            SugraUndervaluedLargeCapsData.model_validate(d) for d in sort_records(data, query.sort)
        ]
