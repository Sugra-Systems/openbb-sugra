"""Sugra Overnight Bank Funding Rate Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.overnight_bank_funding_rate import (
    OvernightBankFundingRateData,
    OvernightBankFundingRateQueryParams,
)

# One FRED series per field; the rate + percentiles are percents (stored as a
# fraction, value / 100), volume is a notional dollar amount kept as-is.
_ID_TO_FIELD = {
    "OBFR": "rate",
    "OBFR1": "percentile_1",
    "OBFR25": "percentile_25",
    "OBFR75": "percentile_75",
    "OBFR99": "percentile_99",
    "OBFRVOL": "volume",
}
_PERCENT_FIELDS = {"rate", "percentile_1", "percentile_25", "percentile_75", "percentile_99"}


class SugraOvernightBankFundingRateQueryParams(OvernightBankFundingRateQueryParams):
    """Sugra Overnight Bank Funding Rate Query Parameters."""


class SugraOvernightBankFundingRateData(OvernightBankFundingRateData):
    """Sugra Overnight Bank Funding Rate Data."""


class SugraOvernightBankFundingRateFetcher(
    Fetcher[
        SugraOvernightBankFundingRateQueryParams,
        list[SugraOvernightBankFundingRateData],
    ]
):
    """Fetch the Overnight Bank Funding Rate and its distribution from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraOvernightBankFundingRateQueryParams:
        """Transform the query parameters."""
        return SugraOvernightBankFundingRateQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraOvernightBankFundingRateQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the six OBFR distribution series from the Sugra API."""
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
        query: SugraOvernightBankFundingRateQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraOvernightBankFundingRateData]:
        """Pivot the six series per date (rate + percentiles /100; volume as-is)."""
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
            raise EmptyDataError("No Overnight Bank Funding Rate observations returned.")
        return [SugraOvernightBankFundingRateData.model_validate(r) for r in rows]
