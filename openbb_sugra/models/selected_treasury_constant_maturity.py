"""Sugra Selected Treasury Constant Maturity (minus Fed Funds) Spread Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.ffrmc import (
    SelectedTreasuryConstantMaturityData,
    SelectedTreasuryConstantMaturityQueryParams,
)

# Selected Treasury Constant Maturity minus the federal funds rate, one FRED
# series each (maturity selects).
_MATURITY_TO_SERIES = {
    "10y": "T10YFF",
    "5y": "T5YFF",
    "1y": "T1YFF",
    "6m": "T6MFF",
    "3m": "T3MFF",
}
_DEFAULT = "10y"


class SugraSelectedTreasuryConstantMaturityQueryParams(
    SelectedTreasuryConstantMaturityQueryParams
):
    """Sugra Selected Treasury Constant Maturity Query Parameters."""


class SugraSelectedTreasuryConstantMaturityData(SelectedTreasuryConstantMaturityData):
    """Sugra Selected Treasury Constant Maturity Data."""


class SugraSelectedTreasuryConstantMaturityFetcher(
    Fetcher[
        SugraSelectedTreasuryConstantMaturityQueryParams,
        list[SugraSelectedTreasuryConstantMaturityData],
    ]
):
    """Fetch the Treasury Constant Maturity minus EFFR spread (T*FF) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraSelectedTreasuryConstantMaturityQueryParams:
        """Transform the query parameters."""
        return SugraSelectedTreasuryConstantMaturityQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraSelectedTreasuryConstantMaturityQueryParams,
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
        query: SugraSelectedTreasuryConstantMaturityQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraSelectedTreasuryConstantMaturityData]:
        """Validate into the standard model (the rate is an as-is percent)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows = fred_observations(data)
        if not rows:
            raise EmptyDataError("No Selected Treasury Constant Maturity observations returned.")
        return [
            SugraSelectedTreasuryConstantMaturityData.model_validate(
                {"date": r["date"], "rate": r["value"]}
            )
            for r in rows
        ]
