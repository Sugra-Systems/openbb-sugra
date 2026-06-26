"""Sugra Fama-French International Index Returns Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_famafrench.models.international_index_returns import (
    FamaFrenchInternationalIndexReturnsData,
    FamaFrenchInternationalIndexReturnsQueryParams,
)

# Pull the full series so transform_data can window by date without the API
# silently dropping the oldest rows (matches the Sugra API ceiling le=30000).
_FULL_SERIES_LIMIT = 30000


class SugraFamaFrenchInternationalIndexReturnsFetcher(
    Fetcher[
        FamaFrenchInternationalIndexReturnsQueryParams,
        list[FamaFrenchInternationalIndexReturnsData],
    ]
):
    """Fetch Fama-French international index portfolio returns from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> FamaFrenchInternationalIndexReturnsQueryParams:
        """Transform the query parameters."""
        return FamaFrenchInternationalIndexReturnsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FamaFrenchInternationalIndexReturnsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the wide international index records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(
            "/api/v1/fama-french/international-index",
            api_key,
            {
                "index": query.index,
                "measure": query.measure,
                "frequency": query.frequency,
                # The Sugra API defaults both flags to True; the OpenBB query params
                # default to None, which the native model also treats as True.
                "dividends": True if query.dividends is None else query.dividends,
                "required": (
                    True
                    if query.all_data_items_required is None
                    else query.all_data_items_required
                ),
                "limit": _FULL_SERIES_LIMIT,
            },
        )
        payload = envelope_data(response)
        return payload.get("records", []) if isinstance(payload, dict) else []

    @staticmethod
    def transform_data(
        query: FamaFrenchInternationalIndexReturnsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FamaFrenchInternationalIndexReturnsData]:
        """Normalise the period token, window by date, validate one row per period.

        The Sugra API already returns the flattened snake-cased columns (mkt,
        be_me_high, ...) that match the model fields, so each record validates
        directly (the model is populate_by_name) - no melt, unlike the sorted
        US / regional portfolios.
        """
        # pylint: disable=import-outside-toplevel
        from datetime import date as _date

        from openbb_core.provider.utils.errors import EmptyDataError
        from pydantic import ValidationError

        from openbb_sugra.utils.helpers import kf_period_to_iso

        if not data:
            raise EmptyDataError("No Fama-French international index records returned.")

        start = query.start_date
        end = query.end_date

        rows: list[FamaFrenchInternationalIndexReturnsData] = []
        for rec in data:
            if not isinstance(rec, dict) or rec.get("date") is None:
                continue
            iso = kf_period_to_iso(str(rec["date"]))
            try:
                period = _date.fromisoformat(iso)
            except ValueError:
                continue
            if (start and period < start) or (end and period > end):
                continue
            try:
                rows.append(
                    FamaFrenchInternationalIndexReturnsData.model_validate(
                        {**rec, "date": iso}
                    )
                )
            except ValidationError:
                continue

        if not rows:
            raise EmptyDataError(
                "No Fama-French international index records matched the query."
            )
        rows.sort(key=lambda r: r.date)
        return rows
