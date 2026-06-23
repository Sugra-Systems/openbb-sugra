"""Sugra Port Info Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.port_info import (
    PortInfoData,
    PortInfoQueryParams,
)
from pydantic import Field


class SugraPortInfoQueryParams(PortInfoQueryParams):
    """Sugra Port Info Query Parameters."""


class SugraPortInfoData(PortInfoData):
    """Sugra Port Info Data."""

    name: str | None = Field(default=None, description="Name of the port.")
    country: str | None = Field(default=None, description="Country the port is located in.")
    iso3: str | None = Field(
        default=None, description="ISO 3166-1 alpha-3 country code.", alias="ISO3"
    )
    continent: str | None = Field(default=None, description="Continent of the port.")
    fullname: str | None = Field(default=None, description="Full descriptive name of the port.")
    latitude: float | None = Field(default=None, description="Latitude of the port.", alias="lat")
    longitude: float | None = Field(default=None, description="Longitude of the port.", alias="lon")
    vessel_count_total: int | None = Field(
        default=None, description="Total number of vessels recorded at the port."
    )


class SugraPortInfoFetcher(Fetcher[SugraPortInfoQueryParams, list[SugraPortInfoData]]):
    """Fetch the port catalog from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraPortInfoQueryParams:
        """Transform the query parameters."""
        return SugraPortInfoQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraPortInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw port catalog from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/maritime/ports", api_key)
        payload = envelope_data(response)
        rows = payload.get("ports", []) if isinstance(payload, dict) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraPortInfoQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraPortInfoData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No ports returned.")

        results: list[SugraPortInfoData] = []
        for item in data:
            code = item.get("portid")
            if code is None:
                continue
            results.append(
                SugraPortInfoData.model_validate(
                    {
                        "port_code": str(code),
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
            raise EmptyDataError("No port rows produced.")
        return results
