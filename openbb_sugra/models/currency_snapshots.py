"""Sugra Currency Snapshots Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.currency_snapshots import (
    CurrencySnapshotsData,
    CurrencySnapshotsQueryParams,
)
from pydantic import Field


class SugraCurrencySnapshotsQueryParams(CurrencySnapshotsQueryParams):
    """Sugra Currency Snapshots Query Parameters."""


class SugraCurrencySnapshotsData(CurrencySnapshotsData):
    """Sugra Currency Snapshots Data."""

    date: str | None = Field(default=None, description="Reference date of the rate snapshot.")


class SugraCurrencySnapshotsFetcher(
    Fetcher[SugraCurrencySnapshotsQueryParams, list[SugraCurrencySnapshotsData]]
):
    """Fetch the latest forex reference rates from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCurrencySnapshotsQueryParams:
        """Transform the query parameters."""
        return SugraCurrencySnapshotsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCurrencySnapshotsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the latest rates snapshot from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)

        params: dict[str, Any] = {}
        counters = query.counter_currencies
        if counters:
            params["symbols"] = counters if isinstance(counters, str) else ",".join(counters)

        response = await sugra_get("/api/v1/forex/latest", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraCurrencySnapshotsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraCurrencySnapshotsData]:
        """Explode the rates map into per-counter-currency snapshot rows."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        base = (data or {}).get("base") or "EUR"
        ref_date = (data or {}).get("date")
        rates = (data or {}).get("rates") or {}
        if not rates:
            raise EmptyDataError("No currency snapshot rates returned.")

        rows: list[SugraCurrencySnapshotsData] = []
        for counter, rate in rates.items():
            if rate is None:
                continue
            rows.append(
                SugraCurrencySnapshotsData(
                    base_currency=base,
                    counter_currency=counter,
                    last_rate=rate,
                    close=rate,
                    date=ref_date,
                )
            )

        if not rows:
            raise EmptyDataError("No currency snapshot rows produced.")
        return rows
