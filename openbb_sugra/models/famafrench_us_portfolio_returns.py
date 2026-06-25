"""Sugra Fama-French US Portfolio Returns Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_famafrench.models.us_portfolio_returns import (
    FamaFrenchUSPortfolioReturnsData,
    FamaFrenchUSPortfolioReturnsQueryParams,
)

# Pull the full series so transform_data can window by date without the API
# silently dropping the oldest rows. Matches the Sugra API ceiling (le=30000),
# which spans the longest daily portfolio history (~25k trading days since 1926).
_FULL_SERIES_LIMIT = 30000


class SugraFamaFrenchUSPortfolioReturnsFetcher(
    Fetcher[
        FamaFrenchUSPortfolioReturnsQueryParams,
        list[FamaFrenchUSPortfolioReturnsData],
    ]
):
    """Fetch Fama-French US portfolio returns from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> FamaFrenchUSPortfolioReturnsQueryParams:
        """Transform the query parameters."""
        return FamaFrenchUSPortfolioReturnsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FamaFrenchUSPortfolioReturnsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the wide portfolio records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        # The Sugra API resolves frequency itself (daily / weekly files ignore it),
        # selects the measure sub-table, and returns wide records (one row per
        # period with a column per portfolio formation). transform_data melts +
        # windows, so pull the whole series here.
        response = await sugra_get(
            "/api/v1/fama-french/us-portfolio",
            api_key,
            {
                "portfolio": query.portfolio,
                "measure": query.measure,
                "frequency": query.frequency,
                "limit": _FULL_SERIES_LIMIT,
            },
        )
        payload = envelope_data(response)
        return payload.get("records", []) if isinstance(payload, dict) else []

    @staticmethod
    def transform_data(
        query: FamaFrenchUSPortfolioReturnsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FamaFrenchUSPortfolioReturnsData]:
        """Melt the wide records to the standard long shape, window, validate."""
        # pylint: disable=import-outside-toplevel
        from datetime import date as _date

        from openbb_core.provider.utils.errors import EmptyDataError
        from pydantic import ValidationError

        from openbb_sugra.utils.helpers import kf_period_to_iso

        if not data:
            raise EmptyDataError("No Fama-French portfolio records returned.")

        start = query.start_date
        end = query.end_date

        rows: list[FamaFrenchUSPortfolioReturnsData] = []
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
            for formation, value in rec.items():
                if formation == "date" or value is None:
                    continue
                try:
                    rows.append(
                        FamaFrenchUSPortfolioReturnsData.model_validate({
                            "date": iso,
                            "portfolio": formation,
                            "measure": query.measure,
                            "value": value,
                        })
                    )
                except ValidationError:
                    continue

        if not rows:
            raise EmptyDataError("No Fama-French portfolio records matched the query.")
        # The Sugra API returns newest-first; the standard model orders ascending.
        rows.sort(key=lambda r: (r.date, r.portfolio))
        return rows
