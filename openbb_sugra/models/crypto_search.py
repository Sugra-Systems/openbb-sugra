"""Sugra Crypto Search Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.crypto_search import (
    CryptoSearchData,
    CryptoSearchQueryParams,
)
from pydantic import Field


class SugraCryptoSearchQueryParams(CryptoSearchQueryParams):
    """Sugra Crypto Search Query Parameters."""


class SugraCryptoSearchData(CryptoSearchData):
    """Sugra Crypto Search Data."""

    coin_id: str | None = Field(
        default=None,
        description="Sugra coin id used for crypto history lookups.",
        alias="id",
    )


class SugraCryptoSearchFetcher(Fetcher[SugraCryptoSearchQueryParams, list[SugraCryptoSearchData]]):
    """Search the Sugra crypto coin universe."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCryptoSearchQueryParams:
        """Transform the query parameters."""
        return SugraCryptoSearchQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCryptoSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the coin list from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/crypto/coins", api_key)
        payload = envelope_data(response)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        return items or []

    @staticmethod
    def transform_data(
        query: SugraCryptoSearchQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCryptoSearchData]:
        """Validate, optionally filter by query, and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No crypto coins returned.")

        rows = data
        if query.query:
            needle = query.query.lower()
            rows = [
                r
                for r in data
                if needle in str(r.get("name", "")).lower()
                or needle in str(r.get("symbol", "")).lower()
                or needle in str(r.get("id", "")).lower()
            ]
        if not rows:
            raise EmptyDataError("No crypto coins matched the search query.")

        return [SugraCryptoSearchData.model_validate(r) for r in rows]
