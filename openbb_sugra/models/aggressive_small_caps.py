"""Sugra Aggressive Small Caps Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_performance import (
    EquityPerformanceData,
    EquityPerformanceQueryParams,
)


class SugraEquityAggressiveSmallCapsQueryParams(EquityPerformanceQueryParams):
    """Sugra Aggressive Small Caps Query Parameters."""


class SugraEquityAggressiveSmallCapsData(EquityPerformanceData):
    """Sugra Aggressive Small Caps Data."""


class SugraEquityAggressiveSmallCapsFetcher(
    Fetcher[
        SugraEquityAggressiveSmallCapsQueryParams,
        list[SugraEquityAggressiveSmallCapsData],
    ]
):
    """Fetch aggressive small-cap equities from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraEquityAggressiveSmallCapsQueryParams:
        """Transform the query parameters."""
        return SugraEquityAggressiveSmallCapsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityAggressiveSmallCapsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw aggressive small-cap records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models._screener_base import fetch_predefined

        return await fetch_predefined("aggressive_small_caps", credentials)

    @staticmethod
    def transform_data(
        query: SugraEquityAggressiveSmallCapsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityAggressiveSmallCapsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.models._screener_base import sort_records

        if not data:
            raise EmptyDataError("No aggressive small-cap data returned.")
        return [
            SugraEquityAggressiveSmallCapsData.model_validate(d)
            for d in sort_records(data, query.sort)
        ]
