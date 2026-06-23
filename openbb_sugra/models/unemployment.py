"""Sugra Unemployment Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.unemployment import (
    UnemploymentData,
    UnemploymentQueryParams,
)

_SERIES_ID = "UNRATE"
_COUNTRY = "united_states"


class SugraUnemploymentQueryParams(UnemploymentQueryParams):
    """Sugra Unemployment Query Parameters."""


class SugraUnemploymentData(UnemploymentData):
    """Sugra Unemployment Data."""


class SugraUnemploymentFetcher(Fetcher[SugraUnemploymentQueryParams, list[SugraUnemploymentData]]):
    """Fetch the US unemployment rate (UNRATE) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraUnemploymentQueryParams:
        """Transform the query parameters."""
        return SugraUnemploymentQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraUnemploymentQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw UNRATE series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        response = await sugra_get(f"/api/v1/fred/series/{_SERIES_ID}", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraUnemploymentQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraUnemploymentData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        observations = (data or {}).get("observations") or []
        if not observations:
            raise EmptyDataError("No unemployment observations returned.")
        rows: list[SugraUnemploymentData] = []
        for obs in observations:
            if not isinstance(obs, dict) or obs.get("date") is None:
                continue
            value = obs.get("value")
            if isinstance(value, str):
                if value.strip() in {"", "."}:
                    continue
                value = float(value)
            if value is None:
                continue
            rows.append(
                SugraUnemploymentData.model_validate(
                    {"date": obs["date"], "country": _COUNTRY, "value": value}
                )
            )
        if not rows:
            raise EmptyDataError("No unemployment observations matched the query.")
        return rows
