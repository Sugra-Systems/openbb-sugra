"""Sugra Crypto Historical Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.crypto_historical import (
    CryptoHistoricalData,
    CryptoHistoricalQueryParams,
)
from pydantic import Field

# Buckets the Sugra crypto history endpoint accepts for the `days` parameter.
_DAYS_BUCKETS = [1, 7, 14, 30, 90, 180, 365]


class SugraCryptoHistoricalQueryParams(CryptoHistoricalQueryParams):
    """Sugra Crypto Historical Query Parameters."""


class SugraCryptoHistoricalData(CryptoHistoricalData):
    """Sugra Crypto Historical Data.

    The Sugra crypto history endpoint returns a price series (price, market cap,
    total volume) rather than OHLCV bars. `close` is mapped from `price` and
    `volume` from `total_volume`; open/high/low are not provided.
    """

    market_cap: float | None = Field(
        default=None,
        description="Market capitalization at the observation timestamp.",
    )


class SugraCryptoHistoricalFetcher(
    Fetcher[SugraCryptoHistoricalQueryParams, list[SugraCryptoHistoricalData]]
):
    """Fetch a crypto price series from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCryptoHistoricalQueryParams:
        """Transform the query parameters."""
        return SugraCryptoHistoricalQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCryptoHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw price series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from datetime import date as dateType

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)

        # The endpoint keys on the Sugra coin id (e.g. "bitcoin"), lower-case.
        coin_id = query.symbol.lower().replace("/", "")

        # Map the requested window to the nearest accepted bucket.
        days = "365"
        if query.start_date:
            end = query.end_date or dateType.today()
            span = (end - query.start_date).days
            chosen = next((b for b in _DAYS_BUCKETS if b >= span), 365)
            days = str(chosen)

        response = await sugra_get(f"/api/v1/crypto/{coin_id}/history", api_key, {"days": days})
        payload = envelope_data(response)
        rows = payload if isinstance(payload, list) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraCryptoHistoricalQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCryptoHistoricalData]:
        """Validate and transform the price series into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No crypto history returned for the symbol.")

        results: list[SugraCryptoHistoricalData] = []
        for row in data:
            ts = row.get("timestamp")
            price = row.get("price")
            if ts is None or price is None:
                continue
            results.append(
                SugraCryptoHistoricalData(
                    date=ts,
                    close=price,
                    volume=row.get("total_volume"),
                    market_cap=row.get("market_cap"),
                )
            )

        # Honour an explicit start_date filter (endpoint only takes a bucket).
        if query.start_date:
            results = [
                r
                for r in results
                if (r.date.date() if hasattr(r.date, "date") else r.date) >= query.start_date
            ]
        if query.end_date:
            results = [
                r
                for r in results
                if (r.date.date() if hasattr(r.date, "date") else r.date) <= query.end_date
            ]

        if not results:
            raise EmptyDataError("No crypto history rows after filtering.")
        return results
