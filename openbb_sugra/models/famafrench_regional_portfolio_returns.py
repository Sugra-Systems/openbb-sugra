"""Sugra Fama-French Regional Portfolio Returns Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_famafrench.models.regional_portfolio_returns import (
    FamaFrenchRegionalPortfolioReturnsData,
    FamaFrenchRegionalPortfolioReturnsQueryParams,
)

# Pull the full series so transform_data can window by date without the API
# silently dropping the oldest rows (matches the Sugra API ceiling le=30000).
_FULL_SERIES_LIMIT = 30000


class SugraFamaFrenchRegionalPortfolioReturnsFetcher(
    Fetcher[
        FamaFrenchRegionalPortfolioReturnsQueryParams,
        list[FamaFrenchRegionalPortfolioReturnsData],
    ]
):
    """Fetch Fama-French regional portfolio returns from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> FamaFrenchRegionalPortfolioReturnsQueryParams:
        """Transform the query parameters."""
        return FamaFrenchRegionalPortfolioReturnsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FamaFrenchRegionalPortfolioReturnsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the wide regional portfolio records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(
            "/api/v1/fama-french/regional-portfolio",
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
        query: FamaFrenchRegionalPortfolioReturnsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FamaFrenchRegionalPortfolioReturnsData]:
        """Melt the wide records to the standard long shape, window, validate."""
        # pylint: disable=import-outside-toplevel
        from datetime import date as _date

        from openbb_core.provider.utils.errors import EmptyDataError
        from pydantic import ValidationError

        from openbb_sugra.utils.helpers import kf_period_to_iso

        if not data:
            raise EmptyDataError("No Fama-French regional portfolio records returned.")

        start = query.start_date
        end = query.end_date

        rows: list[FamaFrenchRegionalPortfolioReturnsData] = []
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
                        FamaFrenchRegionalPortfolioReturnsData.model_validate({
                            "date": iso,
                            "portfolio": formation,
                            "measure": query.measure,
                            "value": value,
                        })
                    )
                except ValidationError:
                    continue

        if not rows:
            raise EmptyDataError(
                "No Fama-French regional portfolio records matched the query."
            )
        rows.sort(key=lambda r: (r.date, r.portfolio))
        return rows
