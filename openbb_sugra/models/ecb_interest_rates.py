"""Sugra European Central Bank Interest Rates Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.ecb_interest_rates import (
    EuropeanCentralBankInterestRatesData,
    EuropeanCentralBankInterestRatesParams,
)

# The three ECB key rates, one FRED series each (interest_rate_type selects).
_RATE_TYPE_TO_SERIES = {
    "deposit": "ECBDFR",
    "lending": "ECBMLFR",
    "refinancing": "ECBMRRFR",
}
_DEFAULT = "lending"


class SugraECBInterestRatesQueryParams(EuropeanCentralBankInterestRatesParams):
    """Sugra European Central Bank Interest Rates Query Parameters."""


class SugraECBInterestRatesData(EuropeanCentralBankInterestRatesData):
    """Sugra European Central Bank Interest Rates Data."""


class SugraECBInterestRatesFetcher(
    Fetcher[SugraECBInterestRatesQueryParams, list[SugraECBInterestRatesData]]
):
    """Fetch the ECB deposit/lending/refinancing key rate from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraECBInterestRatesQueryParams:
        """Transform the query parameters."""
        return SugraECBInterestRatesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraECBInterestRatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw ECB key-rate series for the chosen type from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        series_id = _RATE_TYPE_TO_SERIES[query.interest_rate_type or _DEFAULT]
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
        query: SugraECBInterestRatesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraECBInterestRatesData]:
        """Validate into the standard model (the rate is an as-is percent)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows = fred_observations(data)
        if not rows:
            raise EmptyDataError("No ECB interest rate observations returned.")
        return [
            SugraECBInterestRatesData.model_validate({"date": r["date"], "rate": r["value"]})
            for r in rows
        ]
