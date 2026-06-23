"""Sugra Maritime Chokepoint Info Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.maritime_chokepoint_info import (
    MaritimeChokePointInfoData,
    MaritimeChokePointInfoQueryParams,
)
from pydantic import Field


class SugraMaritimeChokePointInfoQueryParams(MaritimeChokePointInfoQueryParams):
    """Sugra Maritime Chokepoint Info Query Parameters."""


class SugraMaritimeChokePointInfoData(MaritimeChokePointInfoData):
    """Sugra Maritime Chokepoint Info Data."""

    name: str | None = Field(default=None, description="Name of the chokepoint.")
    country: str | None = Field(
        default=None, description="Country the chokepoint is associated with."
    )
    iso3: str | None = Field(
        default=None, description="ISO 3166-1 alpha-3 country code.", alias="ISO3"
    )
    continent: str | None = Field(default=None, description="Continent of the chokepoint.")
    fullname: str | None = Field(
        default=None, description="Full descriptive name of the chokepoint."
    )
    latitude: float | None = Field(
        default=None, description="Latitude of the chokepoint.", alias="lat"
    )
    longitude: float | None = Field(
        default=None, description="Longitude of the chokepoint.", alias="lon"
    )
    vessel_count_total: int | None = Field(
        default=None, description="Total number of vessels recorded at the chokepoint."
    )


class SugraMaritimeChokePointInfoFetcher(
    Fetcher[
        SugraMaritimeChokePointInfoQueryParams,
        list[SugraMaritimeChokePointInfoData],
    ]
):
    """Fetch the maritime chokepoint catalog from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraMaritimeChokePointInfoQueryParams:
        """Transform the query parameters."""
        return SugraMaritimeChokePointInfoQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraMaritimeChokePointInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw chokepoint catalog from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/maritime/chokepoints", api_key)
        payload = envelope_data(response)
        rows = payload.get("chokepoints", []) if isinstance(payload, dict) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraMaritimeChokePointInfoQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraMaritimeChokePointInfoData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No maritime chokepoints returned.")

        results: list[SugraMaritimeChokePointInfoData] = []
        for item in data:
            code = item.get("portid")
            if code is None:
                continue
            results.append(
                SugraMaritimeChokePointInfoData.model_validate(
                    {
                        "chokepoint_code": str(code),
                        "name": item.get("portname"),
                        "country": item.get("country"),
                        "ISO3": item.get("ISO3"),
                        "continent": item.get("continent"),
                        "fullname": item.get("fullname"),
                        "lat": item.get("lat"),
                        "lon": item.get("lon"),
                        "vessel_count_total": item.get("vessel_count_total"),
                    }
                )
            )

        if not results:
            raise EmptyDataError("No maritime chokepoint rows produced.")
        return results
