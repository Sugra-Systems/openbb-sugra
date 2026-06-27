"""Sugra Country Profile Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.country_profile import (
    CountryProfileData,
    CountryProfileQueryParams,
)
from pydantic import Field


class SugraCountryProfileQueryParams(CountryProfileQueryParams):
    """Sugra Country Profile Query Parameters."""

    __json_schema_extra__ = {"country": {"multiple_items_allowed": True}}

    latest: bool = Field(
        default=True,
        description="If True, return only the latest data point per country.",
    )


class SugraCountryProfileData(CountryProfileData):
    """Sugra Country Profile Data."""

    date: dateType | None = Field(
        default=None,
        description="Observation date (present only when latest=False history is requested).",
    )


class SugraCountryProfileFetcher(
    Fetcher[SugraCountryProfileQueryParams, list[SugraCountryProfileData]]
):
    """Fetch macroeconomic country profiles from the Sugra API.

    Backed by /api/v1/macro/country-profile, which assembles each country's
    profile server-side in one batched upstream call per country (cached 24h).
    Percent fields are already normalized to fractions; gdp_usd is in billions.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCountryProfileQueryParams:
        """Transform the query parameters."""
        return SugraCountryProfileQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCountryProfileQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw country-profile payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {"country": query.country}
        if not query.latest:
            params["latest"] = "false"
        response = await sugra_get("/api/v1/macro/country-profile", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraCountryProfileQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraCountryProfileData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        results = (data or {}).get("results") or []
        if not results:
            raise EmptyDataError("No country profile data returned.")
        return [
            SugraCountryProfileData.model_validate(r)
            for r in results
            if isinstance(r, dict) and r.get("country")
        ]
