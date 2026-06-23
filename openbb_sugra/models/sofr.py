"""Sugra SOFR Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.sofr import SOFRData, SOFRQueryParams


class SugraSOFRQueryParams(SOFRQueryParams):
    """Sugra SOFR Query Parameters."""


class SugraSOFRData(SOFRData):
    """Sugra SOFR Data."""


class SugraSOFRFetcher(Fetcher[SugraSOFRQueryParams, list[SugraSOFRData]]):
    """Fetch the Secured Overnight Financing Rate from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraSOFRQueryParams:
        """Transform the query parameters."""
        return SugraSOFRQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraSOFRQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw SOFR series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        response = await sugra_get("/api/v1/fred/series/SOFR", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraSOFRQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraSOFRData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        observations = (data or {}).get("observations") or []
        if not observations:
            raise EmptyDataError("No SOFR observations returned.")
        rows: list[SugraSOFRData] = []
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
            rows.append(SugraSOFRData.model_validate({"date": obs["date"], "rate": value}))
        if not rows:
            raise EmptyDataError("No SOFR observations matched the query.")
        return rows
