"""Sugra Export Destinations Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.export_destinations import (
    ExportDestinationsData,
    ExportDestinationsQueryParams,
)
from pydantic import Field


class SugraExportDestinationsQueryParams(ExportDestinationsQueryParams):
    """Sugra Export Destinations Query Parameters."""

    __json_schema_extra__ = {"country": {"multiple_items_allowed": True}}


class SugraExportDestinationsData(ExportDestinationsData):
    """Sugra Export Destinations Data."""

    units: str | None = Field(default=None, description="The units of measurement for the value.")
    title: str | None = Field(default=None, description="The title of the data.")
    footnote: str | None = Field(default=None, description="The footnote for the data.")


class SugraExportDestinationsFetcher(
    Fetcher[SugraExportDestinationsQueryParams, list[SugraExportDestinationsData]]
):
    """Fetch top export destinations by country from the Sugra API.

    Backed by /api/v1/macro/exports/destinations, which resolves the country and
    fetches each one's destination breakdown server-side (one upstream call per
    country, bounded + cached). Fields match the standard model directly.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraExportDestinationsQueryParams:
        """Transform the query parameters."""
        return SugraExportDestinationsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraExportDestinationsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw export-destination payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(
            "/api/v1/macro/exports/destinations", api_key, {"country": query.country}
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraExportDestinationsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraExportDestinationsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        results = (data or {}).get("results") or []
        if not results:
            raise EmptyDataError("No export destinations returned.")
        return [
            SugraExportDestinationsData.model_validate(r)
            for r in results
            if isinstance(r, dict)
            and r.get("origin_country")
            and r.get("destination_country")
            and r.get("value") is not None
        ]
