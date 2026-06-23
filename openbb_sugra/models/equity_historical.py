"""Sugra Equity Historical Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_historical import (
    EquityHistoricalData,
    EquityHistoricalQueryParams,
)
from pydantic import Field


class SugraEquityHistoricalQueryParams(EquityHistoricalQueryParams):
    """Sugra Equity Historical Query Parameters."""

    interval: str = Field(
        default="1d",
        description="Data granularity. One of 1m, 5m, 15m, 1h, 1d, 1wk, 1mo.",
    )


class SugraEquityHistoricalData(EquityHistoricalData):
    """Sugra Equity Historical Data."""

    adj_close: float | None = Field(
        default=None,
        description="Adjusted closing price (splits and dividends).",
    )


class SugraEquityHistoricalFetcher(
    Fetcher[SugraEquityHistoricalQueryParams, list[SugraEquityHistoricalData]]
):
    """Fetch equity OHLCV history from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquityHistoricalQueryParams:
        """Transform the query parameters."""
        return SugraEquityHistoricalQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw OHLCV bars from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {"interval": query.interval}
        if query.start_date or query.end_date:
            if query.start_date:
                params["start"] = query.start_date.strftime("%Y-%m-%d")
            if query.end_date:
                params["end"] = query.end_date.strftime("%Y-%m-%d")
        else:
            params["period"] = "1y"

        response = await sugra_get(
            f"/api/v2/quotes/{query.symbol.upper()}/historical", api_key, params
        )
        payload = envelope_data(response)
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraEquityHistoricalQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityHistoricalData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No historical data returned for the symbol.")
        return [SugraEquityHistoricalData.model_validate(d) for d in data]
