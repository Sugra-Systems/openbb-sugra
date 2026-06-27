"""Sugra Treasury Rates Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.treasury_rates import (
    TreasuryRatesData,
    TreasuryRatesQueryParams,
)

# One FRED constant-maturity (DGS*) series per tenor field. Every Treasury rate
# field is a normalized percent (json_schema_extra x-frontend_multiply: 100 on
# every field), so each raw value is stored as a fraction (value / 100). The
# standard model's week_4 has no constant-maturity DGS series, so it stays None.
_ID_TO_FIELD = {
    "DGS1MO": "month_1",
    "DGS2MO": "month_2",
    "DGS3MO": "month_3",
    "DGS6MO": "month_6",
    "DGS1": "year_1",
    "DGS2": "year_2",
    "DGS3": "year_3",
    "DGS5": "year_5",
    "DGS7": "year_7",
    "DGS10": "year_10",
    "DGS20": "year_20",
    "DGS30": "year_30",
}


class SugraTreasuryRatesQueryParams(TreasuryRatesQueryParams):
    """Sugra Treasury Rates Query Parameters."""


class SugraTreasuryRatesData(TreasuryRatesData):
    """Sugra Treasury Rates Data."""


class SugraTreasuryRatesFetcher(
    Fetcher[
        SugraTreasuryRatesQueryParams,
        list[SugraTreasuryRatesData],
    ]
):
    """Fetch the US Treasury constant-maturity rate curve (DGS*) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraTreasuryRatesQueryParams:
        """Transform the query parameters."""
        return SugraTreasuryRatesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraTreasuryRatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the constant-maturity DGS series (one per tenor) from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        return await fred_series_payloads(
            api_key,
            list(_ID_TO_FIELD),
            start_date=query.start_date,
            end_date=query.end_date,
        )

    @staticmethod
    def transform_data(
        query: SugraTreasuryRatesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraTreasuryRatesData]:
        """Pivot the DGS series into one row per date. Every tenor is a fraction (value / 100)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        by_date: dict[str, dict] = {}
        for series_id, payload in (data or {}).items():
            field = _ID_TO_FIELD[series_id]
            for obs in fred_observations(payload):
                # Every Treasury rate field carries x-frontend_multiply: 100, so
                # the normalized percent is the raw value divided by 100.
                by_date.setdefault(obs["date"], {})[field] = obs["value"] / 100

        rows = [{"date": date, **by_date[date]} for date in sorted(by_date)]
        if not rows:
            raise EmptyDataError("No Treasury Rates observations returned.")
        return [SugraTreasuryRatesData.model_validate(r) for r in rows]
