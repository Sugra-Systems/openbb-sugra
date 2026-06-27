"""Sugra Selected Treasury Bill (minus Fed Funds) Spread Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.tbffr import (
    SelectedTreasuryBillData,
    SelectedTreasuryBillQueryParams,
)

# Selected Treasury Bill (secondary market) minus the federal funds rate, one
# monthly FRED series each (maturity selects).
_MATURITY_TO_SERIES = {
    "3m": "TB3SMFFM",
    "6m": "TB6SMFFM",
}
_DEFAULT = "3m"


class SugraSelectedTreasuryBillQueryParams(SelectedTreasuryBillQueryParams):
    """Sugra Selected Treasury Bill Query Parameters."""


class SugraSelectedTreasuryBillData(SelectedTreasuryBillData):
    """Sugra Selected Treasury Bill Data."""


class SugraSelectedTreasuryBillFetcher(
    Fetcher[SugraSelectedTreasuryBillQueryParams, list[SugraSelectedTreasuryBillData]]
):
    """Fetch the Treasury Bill minus EFFR spread (TB3SMFFM / TB6SMFFM) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraSelectedTreasuryBillQueryParams:
        """Transform the query parameters."""
        return SugraSelectedTreasuryBillQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraSelectedTreasuryBillQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw monthly spread series for the chosen maturity from the Sugra API."""
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
        query: SugraSelectedTreasuryBillQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraSelectedTreasuryBillData]:
        """Validate into the standard model (the rate is an as-is percent)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows = fred_observations(data)
        if not rows:
            raise EmptyDataError("No Selected Treasury Bill observations returned.")
        return [
            SugraSelectedTreasuryBillData.model_validate(
                {"date": r["date"], "rate": r["value"]}
            )
            for r in rows
        ]
