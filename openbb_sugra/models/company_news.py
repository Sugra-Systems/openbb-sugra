"""Sugra Company News Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.company_news import (
    CompanyNewsData,
    CompanyNewsQueryParams,
)
from pydantic import Field


class SugraCompanyNewsQueryParams(CompanyNewsQueryParams):
    """Sugra Company News Query Parameters."""


class SugraCompanyNewsData(CompanyNewsData):
    """Sugra Company News Data."""

    source: str | None = Field(default=None, description="Source/publisher name of the article.")


class SugraCompanyNewsFetcher(Fetcher[SugraCompanyNewsQueryParams, list[SugraCompanyNewsData]]):
    """Fetch company-specific news from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCompanyNewsQueryParams:
        """Transform the query parameters."""
        return SugraCompanyNewsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCompanyNewsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw company news from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        symbol = (query.symbol or "").split(",")[0].strip().upper()
        if not symbol:
            from openbb_core.provider.utils.errors import EmptyDataError

            raise EmptyDataError("A symbol is required for company news.")

        params: dict[str, Any] = {}
        if query.limit:
            params["limit"] = query.limit
        response = await sugra_get(f"/api/v2/quotes/{symbol}/news", api_key, params)
        payload = envelope_data(response)
        rows = payload if isinstance(payload, list) else []
        return [{"_symbol": symbol, **r} for r in rows]

    @staticmethod
    def transform_data(
        query: SugraCompanyNewsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCompanyNewsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No company news returned for the symbol.")

        results: list[SugraCompanyNewsData] = []
        for item in data:
            published = item.get("pubDate") or item.get("published")
            title = item.get("title")
            url = item.get("link")
            if not published or not title or not url:
                continue
            results.append(
                SugraCompanyNewsData(
                    date=published,
                    title=title,
                    excerpt=item.get("description"),
                    url=url,
                    symbols=item.get("_symbol"),
                    source=item.get("source"),
                )
            )

        if not results:
            raise EmptyDataError("No company news rows produced.")
        return results
