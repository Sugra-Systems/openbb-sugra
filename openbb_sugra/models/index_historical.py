"""Sugra Index Historical Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.index_historical import (
    IndexHistoricalData,
    IndexHistoricalQueryParams,
)
from pydantic import Field


class SugraIndexHistoricalQueryParams(IndexHistoricalQueryParams):
    """Sugra Index Historical Query Parameters."""

    interval: str = Field(
        default="1d",
        description="Data granularity. One of 1m, 5m, 15m, 1h, 1d, 1wk, 1mo.",
    )


class SugraIndexHistoricalData(IndexHistoricalData):
    """Sugra Index Historical Data."""

    adj_close: float | None = Field(default=None, description="Adjusted closing price.")


class SugraIndexHistoricalFetcher(
    Fetcher[SugraIndexHistoricalQueryParams, list[SugraIndexHistoricalData]]
):
    """Fetch index OHLCV history from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraIndexHistoricalQueryParams:
        """Transform the query parameters."""
        return SugraIndexHistoricalQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraIndexHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw index candles from the Sugra API."""
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

        response = await sugra_get(f"/api/v2/market/chart/{query.symbol.upper()}", api_key, params)
        payload = envelope_data(response)
        candles = payload.get("candles", []) if isinstance(payload, dict) else []
        return candles or []

    @staticmethod
    def transform_data(
        query: SugraIndexHistoricalQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraIndexHistoricalData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No index historical data returned for the symbol.")
        rows = []
        for c in data:
            row = dict(c)
            row["date"] = c.get("timestamp")
            row["symbol"] = query.symbol.upper()
            rows.append(row)
        return [SugraIndexHistoricalData.model_validate(r) for r in rows]
