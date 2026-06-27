"""Sugra Euro Short Term Rate (estr) Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.euro_short_term_rate import (
    EuroShortTermRateData,
    EuroShortTermRateQueryParams,
)

# One FRED series per field. The rate, percentiles and large-bank share are
# percents (stored as a fraction, value / 100); volume (millions EUR),
# transaction count and bank count are kept as-is.
_ID_TO_FIELD = {
    "ECBESTRVOLWGTTRMDMNRT": "rate",
    "ECBESTRRT25THPCTVOL": "percentile_25",
    "ECBESTRRT75THPCTVOL": "percentile_75",
    "ECBESTRTOTVOL": "volume",
    "ECBESTRNUMTRANS": "transactions",
    "ECBESTRNUMACTBANKS": "number_of_banks",
    "ECBESTRSHRVOL5LRGACTBNK": "large_bank_share_of_volume",
}
_PERCENT_FIELDS = {"rate", "percentile_25", "percentile_75", "large_bank_share_of_volume"}
_DEFAULT_START = "2019-10-02"


class SugraEuroShortTermRateQueryParams(EuroShortTermRateQueryParams):
    """Sugra Euro Short Term Rate Query Parameters."""


class SugraEuroShortTermRateData(EuroShortTermRateData):
    """Sugra Euro Short Term Rate Data."""


class SugraEuroShortTermRateFetcher(
    Fetcher[SugraEuroShortTermRateQueryParams, list[SugraEuroShortTermRateData]]
):
    """Fetch the Euro Short Term Rate (ESTR) and its distribution from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEuroShortTermRateQueryParams:
        """Transform the query parameters."""
        return SugraEuroShortTermRateQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEuroShortTermRateQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the seven ESTR distribution series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        return await fred_series_payloads(
            api_key,
            list(_ID_TO_FIELD),
            start_date=query.start_date or _DEFAULT_START,
            end_date=query.end_date,
        )

    @staticmethod
    def transform_data(
        query: SugraEuroShortTermRateQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraEuroShortTermRateData]:
        """Pivot the seven series per date (rate-like fields /100; counts/volume as-is)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        by_date: dict[str, dict] = {}
        for series_id, payload in (data or {}).items():
            field = _ID_TO_FIELD[series_id]
            for obs in fred_observations(payload):
                value = obs["value"] / 100 if field in _PERCENT_FIELDS else obs["value"]
                by_date.setdefault(obs["date"], {})[field] = value

        rows = [
            {"date": date, **by_date[date]}
            for date in sorted(by_date)
            if by_date[date].get("rate") is not None
        ]
        if not rows:
            raise EmptyDataError("No Euro Short Term Rate observations returned.")
        return [SugraEuroShortTermRateData.model_validate(r) for r in rows]
