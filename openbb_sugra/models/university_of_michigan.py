"""Sugra University of Michigan Survey Model."""

# pylint: disable=unused-argument

from datetime import date
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.university_of_michigan import (
    UofMichiganData,
    UofMichiganQueryParams,
)

# Fixed FRED series for the University of Michigan Survey of Consumers.
# UMCSENT  -> consumer_sentiment   : index points (1966:Q1=100), kept as-is.
# MICH     -> inflation_expectation: median expected price change next 12m,
#             a percent (x-frontend_multiply: 100), so stored as a fraction (/100).
_ID_TO_FIELD = {
    "UMCSENT": "consumer_sentiment",
    "MICH": "inflation_expectation",
}
# Legacy pre-1978 sentiment series; merged into consumer_sentiment as a gap fill.
_LEGACY_SENTIMENT_ID = "UMCSENT1"
# Fields whose standard-model schema carries x-frontend_multiply: 100 -> divide by 100.
_PERCENT_FIELDS = {"inflation_expectation"}
# The legacy UMCSENT1 series only matters for history before this cutoff.
_LEGACY_CUTOFF = date(1978, 1, 1)


class SugraUniversityOfMichiganQueryParams(UofMichiganQueryParams):
    """Sugra University of Michigan Survey Query Parameters."""


class SugraUniversityOfMichiganData(UofMichiganData):
    """Sugra University of Michigan Survey Data."""


class SugraUniversityOfMichiganFetcher(
    Fetcher[
        SugraUniversityOfMichiganQueryParams,
        list[SugraUniversityOfMichiganData],
    ]
):
    """Fetch the University of Michigan consumer sentiment and inflation survey."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraUniversityOfMichiganQueryParams:
        """Transform the query parameters."""
        return SugraUniversityOfMichiganQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraUniversityOfMichiganQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the survey series from the Sugra API (3 series by default)."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        ids = list(_ID_TO_FIELD)
        # The modern UMCSENT series starts in 1978; pull the legacy series only
        # when the requested window reaches back before then (or is unbounded).
        if not query.start_date or query.start_date < _LEGACY_CUTOFF:
            ids = ids + [_LEGACY_SENTIMENT_ID]
        return await fred_series_payloads(
            api_key,
            ids,
            start_date=query.start_date,
            end_date=query.end_date,
        )

    @staticmethod
    def transform_data(
        query: SugraUniversityOfMichiganQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraUniversityOfMichiganData]:
        """Pivot per date: sentiment as-is, inflation_expectation /100."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        by_date: dict[str, dict] = {}
        for series_id, field in _ID_TO_FIELD.items():
            for obs in fred_observations((data or {}).get(series_id) or {}):
                value = (
                    obs["value"] / 100 if field in _PERCENT_FIELDS else obs["value"]
                )
                by_date.setdefault(obs["date"], {})[field] = value

        # Combine the legacy series with the modern one: UMCSENT1 (as-is index
        # points) only fills dates where the modern UMCSENT is absent.
        for obs in fred_observations((data or {}).get(_LEGACY_SENTIMENT_ID) or {}):
            row = by_date.setdefault(obs["date"], {})
            if row.get("consumer_sentiment") is None:
                row["consumer_sentiment"] = obs["value"]

        rows = [{"date": d, **by_date[d]} for d in sorted(by_date)]
        if not rows:
            raise EmptyDataError(
                "No University of Michigan survey observations returned."
            )
        return [SugraUniversityOfMichiganData.model_validate(r) for r in rows]
