"""Sugra FRED Series Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.fred_series import (
    SeriesData,
    SeriesQueryParams,
)
from pydantic import Field


class SugraFredSeriesQueryParams(SeriesQueryParams):
    """Sugra FRED Series Query Parameters."""


class SugraFredSeriesData(SeriesData):
    """Sugra FRED Series Data."""

    value: float | None = Field(default=None, description="Observation value for the series.")


class SugraFredSeriesFetcher(Fetcher[SugraFredSeriesQueryParams, list[SugraFredSeriesData]]):
    """Fetch a FRED economic series from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraFredSeriesQueryParams:
        """Transform the query parameters."""
        return SugraFredSeriesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraFredSeriesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw FRED series payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        if query.limit:
            # Sugra's FRED endpoint caps limit at 1000; OpenBB's default is large.
            params["limit"] = min(int(query.limit), 1000)
        response = await sugra_get(f"/api/v1/fred/series/{query.symbol}", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraFredSeriesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraFredSeriesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        observations = (data or {}).get("observations") or []
        if not observations:
            raise EmptyDataError("No FRED observations returned.")
        rows: list[SugraFredSeriesData] = []
        for obs in observations:
            if not isinstance(obs, dict) or obs.get("date") is None:
                continue
            value = obs.get("value")
            if isinstance(value, str):
                value = None if value.strip() in {"", "."} else float(value)
            rows.append(SugraFredSeriesData.model_validate({"date": obs["date"], "value": value}))
        if not rows:
            raise EmptyDataError("No FRED observations matched the query.")
        return rows
