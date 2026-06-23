"""Sugra SONIA Rates Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.sonia_rates import (
    SONIAData,
    SONIAQueryParams,
)


class SugraSONIAQueryParams(SONIAQueryParams):
    """Sugra SONIA Query Parameters."""


class SugraSONIAData(SONIAData):
    """Sugra SONIA Data."""


class SugraSONIAFetcher(Fetcher[SugraSONIAQueryParams, list[SugraSONIAData]]):
    """Fetch the SONIA (Sterling Overnight Index Average) from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraSONIAQueryParams:
        """Transform the query parameters."""
        return SugraSONIAQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraSONIAQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Return the raw SONIA series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/boe/sonia", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, list) else []

    @staticmethod
    def transform_data(
        query: SugraSONIAQueryParams,
        data: list,
        **kwargs: Any,
    ) -> list[SugraSONIAData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from datetime import date as date_type

        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No SONIA observations returned.")
        start = query.start_date
        end = query.end_date
        rows: list[SugraSONIAData] = []
        for obs in data:
            if not isinstance(obs, dict) or obs.get("date") is None:
                continue
            rate = obs.get("IUDSOIA")
            if rate is None:
                continue
            obs_date = obs["date"]
            if start or end:
                try:
                    parsed = date_type.fromisoformat(str(obs_date)[:10])
                except ValueError:
                    parsed = None
                if parsed is not None:
                    if start and parsed < start:
                        continue
                    if end and parsed > end:
                        continue
            rows.append(SugraSONIAData.model_validate({"date": obs_date, "rate": rate}))
        if not rows:
            raise EmptyDataError("No SONIA observations matched the query.")
        return rows
