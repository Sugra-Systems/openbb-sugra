"""Sugra Treasury Constant Maturity (10Y minus shorter) Spread Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.tmc import (
    TreasuryConstantMaturityData,
    TreasuryConstantMaturityQueryParams,
)

# 10-Year Treasury Constant Maturity minus the selected shorter tenor, one
# FRED series each (maturity selects).
_MATURITY_TO_SERIES = {
    "3m": "T10Y3M",
    "2y": "T10Y2Y",
}
_DEFAULT = "3m"


class SugraTreasuryConstantMaturityQueryParams(TreasuryConstantMaturityQueryParams):
    """Sugra Treasury Constant Maturity Query Parameters."""


class SugraTreasuryConstantMaturityData(TreasuryConstantMaturityData):
    """Sugra Treasury Constant Maturity Data."""


class SugraTreasuryConstantMaturityFetcher(
    Fetcher[
        SugraTreasuryConstantMaturityQueryParams,
        list[SugraTreasuryConstantMaturityData],
    ]
):
    """Fetch the 10Y Treasury Constant Maturity spread (T10Y3M / T10Y2Y) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraTreasuryConstantMaturityQueryParams:
        """Transform the query parameters."""
        return SugraTreasuryConstantMaturityQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraTreasuryConstantMaturityQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw spread series for the chosen maturity from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        series_id = _MATURITY_TO_SERIES[query.maturity or _DEFAULT]
        params: dict[str, Any] = {"limit": 1000, "sort_order": "desc"}
        if query.start_date:
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        response = await sugra_get(f"/api/v1/fred/series/{series_id}", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraTreasuryConstantMaturityQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraTreasuryConstantMaturityData]:
        """Validate into the standard model (the rate is an as-is percent)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows = fred_observations(data)
        if not rows:
            raise EmptyDataError("No Treasury Constant Maturity observations returned.")
        return [
            SugraTreasuryConstantMaturityData.model_validate(
                {"date": r["date"], "rate": r["value"]}
            )
            for r in rows
        ]
