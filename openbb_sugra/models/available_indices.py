"""Sugra Available Indices Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.available_indices import (
    AvailableIndicesData,
    AvailableIndicesQueryParams,
)
from pydantic import Field


class SugraAvailableIndicesQueryParams(AvailableIndicesQueryParams):
    """Sugra Available Indices Query Parameters."""


class SugraAvailableIndicesData(AvailableIndicesData):
    """Sugra Available Indices Data."""

    category_group: str | None = Field(
        default=None, description="High-level asset-class group of the index."
    )
    category: str | None = Field(default=None, description="Category of the index.")
    mic: str | None = Field(
        default=None, description="Market Identifier Code of the listing venue."
    )


class SugraAvailableIndicesFetcher(
    Fetcher[SugraAvailableIndicesQueryParams, list[SugraAvailableIndicesData]]
):
    """Fetch the catalog of available indices from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraAvailableIndicesQueryParams:
        """Transform the query parameters."""
        return SugraAvailableIndicesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraAvailableIndicesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw index catalog from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/catalog/indices", api_key)
        payload = envelope_data(response)
        indices = payload.get("indices", []) if isinstance(payload, dict) else []
        return indices or []

    @staticmethod
    def transform_data(
        query: SugraAvailableIndicesQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraAvailableIndicesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No indices returned from the catalog.")
        return [SugraAvailableIndicesData.model_validate(d) for d in data]
