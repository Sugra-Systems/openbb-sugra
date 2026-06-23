"""Sugra World News Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.world_news import (
    WorldNewsData,
    WorldNewsQueryParams,
)
from pydantic import Field


class SugraWorldNewsQueryParams(WorldNewsQueryParams):
    """Sugra World News Query Parameters."""


class SugraWorldNewsData(WorldNewsData):
    """Sugra World News Data."""

    source: str | None = Field(default=None, description="Source/publisher name of the article.")
    region: str | None = Field(default=None, description="Geographic region of the article.")


class SugraWorldNewsFetcher(Fetcher[SugraWorldNewsQueryParams, list[SugraWorldNewsData]]):
    """Fetch world news headlines from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraWorldNewsQueryParams:
        """Transform the query parameters."""
        return SugraWorldNewsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraWorldNewsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw news items from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.limit:
            params["limit"] = query.limit
        response = await sugra_get("/api/v1/news/latest", api_key, params)
        payload = envelope_data(response)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        return items or []

    @staticmethod
    def transform_data(
        query: SugraWorldNewsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraWorldNewsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No world news returned.")

        results: list[SugraWorldNewsData] = []
        for item in data:
            published = item.get("published")
            title = item.get("title")
            if not published or not title:
                continue
            results.append(
                SugraWorldNewsData(
                    date=published,
                    title=title,
                    excerpt=item.get("description"),
                    url=item.get("link"),
                    source=item.get("source_name") or item.get("source"),
                    region=item.get("region"),
                )
            )

        if not results:
            raise EmptyDataError("No world news rows produced.")
        return results
