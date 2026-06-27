"""Sugra FRED Release Table Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.fred_release_table import (
    ReleaseTableData,
    ReleaseTableQueryParams,
)


class SugraReleaseTableQueryParams(ReleaseTableQueryParams):
    """Sugra FRED Release Table Query Parameters."""

    __json_schema_extra__ = {"date": {"multiple_items_allowed": True}}


class SugraReleaseTableData(ReleaseTableData):
    """Sugra FRED Release Table Data."""


class SugraReleaseTableFetcher(
    Fetcher[SugraReleaseTableQueryParams, list[SugraReleaseTableData]]
):
    """Fetch a FRED release table from the Sugra API.

    Backed by the Sugra `/api/v1/fred/release/tables` endpoint, which returns the
    release's hierarchical table tree with inline observation values - ONE call
    per date returns the whole subtree (no per-series fan-out). Omit `element_id`
    to discover the top-level element IDs. `value` is returned in the table's
    native units (no normalization). The endpoint already emits the standard
    field names, so this is a direct map.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraReleaseTableQueryParams:
        """Transform the query parameters."""
        return SugraReleaseTableQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraReleaseTableQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw release-table payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {"release_id": query.release_id}
        if query.element_id is not None:
            params["element_id"] = query.element_id
        if query.date:
            params["date"] = str(query.date)
        response = await sugra_get("/api/v1/fred/release/tables", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraReleaseTableQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraReleaseTableData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        results = (data or {}).get("results") or []
        if not results:
            raise EmptyDataError(
                f"No tables were found for release {query.release_id}. "
                "Use `fred_search` to list release IDs; omit `element_id` to "
                "reveal the top-level element IDs."
            )
        return [
            SugraReleaseTableData.model_validate(r)
            for r in results
            if isinstance(r, dict)
        ]
