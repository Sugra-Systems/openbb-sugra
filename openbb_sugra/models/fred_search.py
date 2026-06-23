"""Sugra FRED Search Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.fred_search import (
    SearchData,
    SearchQueryParams,
)


class SugraFredSearchQueryParams(SearchQueryParams):
    """Sugra FRED Search Query Parameters."""


class SugraFredSearchData(SearchData):
    """Sugra FRED Search Data."""


class SugraFredSearchFetcher(Fetcher[SugraFredSearchQueryParams, list[SugraFredSearchData]]):
    """Search FRED economic series via the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraFredSearchQueryParams:
        """Transform the query parameters."""
        return SugraFredSearchQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraFredSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw macro search payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/macro/search", api_key, {"q": query.query or ""})
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraFredSearchQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraFredSearchData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        series = (data or {}).get("series") or []
        if not series:
            raise EmptyDataError("No FRED series matched the query.")
        rows: list[SugraFredSearchData] = []
        for item in series:
            if not isinstance(item, dict):
                continue
            rows.append(
                SugraFredSearchData.model_validate(
                    {
                        "series_id": item.get("series_id"),
                        "title": item.get("title"),
                        "frequency": item.get("frequency"),
                        "units": item.get("units"),
                        "seasonal_adjustment": item.get("seasonal_adjustment"),
                        "popularity": item.get("popularity"),
                        "observation_start": item.get("observation_start"),
                        "observation_end": item.get("observation_end"),
                    }
                )
            )
        if not rows:
            raise EmptyDataError("No FRED series matched the query.")
        return rows
