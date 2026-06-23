"""Sugra Nominal GDP Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.gdp_nominal import (
    GdpNominalData,
    GdpNominalQueryParams,
)

_SERIES_ID = "GDP"
_COUNTRY = "united_states"


class SugraGdpNominalQueryParams(GdpNominalQueryParams):
    """Sugra Nominal GDP Query Parameters."""


class SugraGdpNominalData(GdpNominalData):
    """Sugra Nominal GDP Data."""


class SugraGdpNominalFetcher(Fetcher[SugraGdpNominalQueryParams, list[SugraGdpNominalData]]):
    """Fetch US Nominal GDP (GDP) from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraGdpNominalQueryParams:
        """Transform the query parameters."""
        return SugraGdpNominalQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraGdpNominalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw GDP series from the Sugra API."""
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
        query: SugraGdpNominalQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraGdpNominalData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        observations = (data or {}).get("observations") or []
        if not observations:
            raise EmptyDataError("No Nominal GDP observations returned.")
        rows: list[SugraGdpNominalData] = []
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
                SugraGdpNominalData.model_validate(
                    {"date": obs["date"], "country": _COUNTRY, "value": value}
                )
            )
        if not rows:
            raise EmptyDataError("No Nominal GDP observations matched the query.")
        return rows
