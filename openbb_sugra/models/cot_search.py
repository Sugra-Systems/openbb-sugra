"""Sugra Commitment of Traders (COT) Search Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.cot_search import (
    CotSearchData,
    CotSearchQueryParams,
)


class SugraCotSearchQueryParams(CotSearchQueryParams):
    """Sugra COT Search Query Parameters."""


class SugraCotSearchData(CotSearchData):
    """Sugra COT Search Data."""


class SugraCotSearchFetcher(Fetcher[SugraCotSearchQueryParams, list[SugraCotSearchData]]):
    """Search Commitment of Traders markets from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCotSearchQueryParams:
        """Transform the query parameters."""
        return SugraCotSearchQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCotSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw COT market matches from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/cot/search", api_key, {"q": query.query or ""})
        payload = envelope_data(response)
        rows = payload.get("markets", []) if isinstance(payload, dict) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraCotSearchQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCotSearchData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No COT markets matched the search query.")

        results: list[SugraCotSearchData] = []
        for item in data:
            market = item.get("market") if isinstance(item, dict) else None
            if not market:
                continue
            results.append(SugraCotSearchData(code=str(market), name=str(market)))

        if not results:
            raise EmptyDataError("No COT search rows produced.")
        return results
