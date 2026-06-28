"""Sugra Futures Historical Price Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.futures_historical import (
    FuturesHistoricalData,
    FuturesHistoricalQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import Field


class SugraFuturesHistoricalQueryParams(FuturesHistoricalQueryParams):
    """Sugra Futures Historical Query Parameters."""

    interval: (
        Literal["1m", "2m", "5m", "15m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
        | None
    ) = Field(default=None, description="The bar interval; defaults to 1d.")


class SugraFuturesHistoricalData(FuturesHistoricalData):
    """Sugra Futures Historical Data."""


class SugraFuturesHistoricalFetcher(
    Fetcher[SugraFuturesHistoricalQueryParams, list[SugraFuturesHistoricalData]]
):
    """Fetch futures OHLCV from the Sugra API.

    Backed by `/api/v2/futures/{root}/historical`. `symbol` is the futures root
    (e.g. CL, GC, ES, ZN). Without `expiration` the continuous front-month series
    is returned; with `expiration` (YYYY-MM) a specific dated contract.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraFuturesHistoricalQueryParams:
        """Transform the query parameters."""
        return SugraFuturesHistoricalQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraFuturesHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw OHLCV rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["start_date"] = str(query.start_date)
        if query.end_date:
            params["end_date"] = str(query.end_date)
        if query.expiration:
            params["expiration"] = query.expiration
        if query.interval:
            params["interval"] = query.interval

        response = await sugra_get(
            f"/api/v2/futures/{query.symbol}/historical", api_key, params
        )
        payload = envelope_data(response)
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        if not rows:
            raise EmptyDataError()
        return rows

    @staticmethod
    def transform_data(
        query: SugraFuturesHistoricalQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraFuturesHistoricalData]:
        """Map the OHLCV rows to the standard model."""
        results: list[SugraFuturesHistoricalData] = []
        for row in data:
            # `close` is required by the standard model; skip an incomplete bar.
            if row.get("close") is None:
                continue
            results.append(
                SugraFuturesHistoricalData.model_validate(
                    {
                        "date": row.get("date"),
                        "open": row.get("open"),
                        "high": row.get("high"),
                        "low": row.get("low"),
                        "close": row.get("close"),
                        "volume": row.get("volume"),
                    }
                )
            )
        if not results:
            raise EmptyDataError()
        return results
