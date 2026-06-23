"""Sugra Trailing Dividend Yield Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.trailing_dividend_yield import (
    TrailingDivYieldData,
    TrailingDivYieldQueryParams,
)


class SugraTrailingDivYieldQueryParams(TrailingDivYieldQueryParams):
    """Sugra Trailing Dividend Yield Query Parameters."""


class SugraTrailingDivYieldData(TrailingDivYieldData):
    """Sugra Trailing Dividend Yield Data."""


class SugraTrailingDivYieldFetcher(
    Fetcher[SugraTrailingDivYieldQueryParams, list[SugraTrailingDivYieldData]]
):
    """Fetch the trailing 12-month dividend yield from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraTrailingDivYieldQueryParams:
        """Transform the query parameters."""
        return SugraTrailingDivYieldQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraTrailingDivYieldQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw dividend summary from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v2/quotes/{query.symbol.upper()}/dividend", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraTrailingDivYieldQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraTrailingDivYieldData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from datetime import datetime, timezone

        from openbb_core.provider.utils.errors import EmptyDataError

        yld = data.get("trailing_annual_dividend_yield") if isinstance(data, dict) else None
        if yld is None:
            yld = data.get("dividend_yield") if isinstance(data, dict) else None
        if yld is None:
            raise EmptyDataError("No trailing dividend yield returned for the symbol.")

        today = datetime.now(timezone.utc).date()
        return [
            SugraTrailingDivYieldData(
                date=today,
                trailing_dividend_yield=yld,
            )
        ]
