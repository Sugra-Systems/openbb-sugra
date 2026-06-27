"""Sugra Federal Funds Rate Projections (FOMC dot plot) Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.fed_projections import (
    PROJECTIONData,
    PROJECTIONQueryParams,
)
from pydantic import Field

# Each projection field is a FRED series; the pair is [current-year, long-run].
_FIELD_TO_IDS = {
    "range_high": ["FEDTARRH", "FEDTARRHLR"],
    "central_tendency_high": ["FEDTARCTH", "FEDTARCTHLR"],
    "median": ["FEDTARMD", "FEDTARMDLR"],
    "range_midpoint": ["FEDTARRM", "FEDTARRMLR"],
    "central_tendency_midpoint": ["FEDTARCTM", "FEDTARCTMLR"],
    "range_low": ["FEDTARRL", "FEDTARRLLR"],
    "central_tendency_low": ["FEDTARCTL", "FEDTARCTLLR"],
}
_FIELDS = list(_FIELD_TO_IDS)


class SugraFedProjectionsQueryParams(PROJECTIONQueryParams):
    """Sugra Federal Funds Rate Projections Query Parameters."""

    long_run: bool = Field(
        default=False, description="Flag to show long run projections."
    )


class SugraFedProjectionsData(PROJECTIONData):
    """Sugra Federal Funds Rate Projections Data."""


class SugraFedProjectionsFetcher(
    Fetcher[SugraFedProjectionsQueryParams, list[SugraFedProjectionsData]]
):
    """Fetch the FOMC Summary of Economic Projections fed funds dot plot (FEDTAR* series)."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraFedProjectionsQueryParams:
        """Transform the query parameters."""
        return SugraFedProjectionsQueryParams(**params)

    @staticmethod
    def _field_to_id(long_run: bool) -> dict[str, str]:
        """Resolve each projection field to its current-year or long-run FRED series."""
        idx = 1 if long_run else 0
        return {field: ids[idx] for field, ids in _FIELD_TO_IDS.items()}

    @staticmethod
    async def aextract_data(
        query: SugraFedProjectionsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the seven projection series for the selected horizon from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        ids = list(SugraFedProjectionsFetcher._field_to_id(query.long_run).values())
        return await fred_series_payloads(api_key, ids)

    @staticmethod
    def transform_data(
        query: SugraFedProjectionsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraFedProjectionsData]:
        """Pivot the projection series into one row per date (rates are as-is percents)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        field_to_id = SugraFedProjectionsFetcher._field_to_id(query.long_run)
        by_date: dict[str, dict] = {}
        for field, series_id in field_to_id.items():
            for obs in fred_observations((data or {}).get(series_id, {})):
                by_date.setdefault(obs["date"], {})[field] = obs["value"]

        if not by_date:
            raise EmptyDataError("No fed funds rate projection observations returned.")
        return [
            SugraFedProjectionsData.model_validate(
                {"date": date, **{field: by_date[date].get(field) for field in _FIELDS}}
            )
            for date in sorted(by_date)
        ]
