"""Sugra BLS Search Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.bls_search import (
    SearchData,
    SearchQueryParams,
)


class SugraBlsSearchQueryParams(SearchQueryParams):
    """Sugra BLS Search Query Parameters."""


class SugraBlsSearchData(SearchData):
    """Sugra BLS Search Data."""


class SugraBlsSearchFetcher(Fetcher[SugraBlsSearchQueryParams, list[SugraBlsSearchData]]):
    """Search the Sugra BLS series catalog."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraBlsSearchQueryParams:
        """Transform the query parameters."""
        return SugraBlsSearchQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraBlsSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw BLS catalog from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/worldbank/bls/catalog", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, list) else []

    @staticmethod
    def transform_data(
        query: SugraBlsSearchQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraBlsSearchData]:
        """Validate, filter by the search term, and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No BLS catalog returned.")

        # The standard model documents ';' as an AND operator across terms, so a
        # row must match EVERY term (against the key or the name) to be kept.
        terms = [t.strip().lower() for t in (query.query or "").split(";") if t.strip()]
        rows: list[SugraBlsSearchData] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            # The catalog key (e.g. "cpi-all") is the identifier the Sugra series
            # endpoint accepts, so it is the round-trippable `symbol`.
            key = item.get("key")
            name = item.get("name")
            if not key:
                continue
            haystack_key = str(key).lower()
            haystack_name = str(name or "").lower()
            if terms and not all(
                t in haystack_key or t in haystack_name for t in terms
            ):
                continue
            rows.append(
                SugraBlsSearchData.model_validate(
                    {"symbol": key, "title": name, "survey_name": "BLS"}
                )
            )

        if not rows:
            raise EmptyDataError("No BLS series matched the search query.")
        return rows
