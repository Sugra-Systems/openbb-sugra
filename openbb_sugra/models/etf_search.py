"""Sugra ETF Search Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.etf_search import (
    EtfSearchData,
    EtfSearchQueryParams,
)
from pydantic import Field


class SugraEtfSearchQueryParams(EtfSearchQueryParams):
    """Sugra ETF Search Query Parameters."""


class SugraEtfSearchData(EtfSearchData):
    """Sugra ETF Search Data."""

    category: str | None = Field(default=None, description="Fund category classification.")
    aum_usd: float | None = Field(
        default=None,
        alias="aum_usd_estimate",
        description="Estimated assets under management, in USD.",
    )


class SugraEtfSearchFetcher(Fetcher[SugraEtfSearchQueryParams, list[SugraEtfSearchData]]):
    """Search the Sugra ETF universe."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEtfSearchQueryParams:
        """Transform the query parameters."""
        return SugraEtfSearchQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEtfSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw ETF universe from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/etf/snapshot/universe", api_key)
        payload = envelope_data(response)
        symbols = payload.get("symbols", []) if isinstance(payload, dict) else []
        return symbols or []

    @staticmethod
    def transform_data(
        query: SugraEtfSearchQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEtfSearchData]:
        """Filter and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No ETF universe returned.")
        needle = (query.query or "").strip().lower()
        rows = data
        if needle:
            rows = [
                d
                for d in data
                if needle in str(d.get("symbol", "")).lower()
                or needle in str(d.get("name", "")).lower()
                or needle in str(d.get("category", "")).lower()
            ]
        if not rows:
            raise EmptyDataError("No ETFs matched the search query.")
        return [SugraEtfSearchData.model_validate(d) for d in rows]
