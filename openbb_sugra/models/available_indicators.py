"""Sugra Available Indicators Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from datetime import datetime
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.available_indicators import (
    AvailableIndicatorsData,
    AvailableIndicesQueryParams,
)
from pydantic import Field


class SugraAvailableIndicatorsQueryParams(AvailableIndicesQueryParams):
    """Sugra Available Indicators Query Parameters."""


class SugraAvailableIndicatorsData(AvailableIndicatorsData):
    """Sugra Available Indicators Data."""

    currency: str | None = Field(
        default=None, description="The currency, or unit, the data is based in."
    )
    scale: str | None = Field(default=None, description="The scale of the data.")
    multiplier: int | None = Field(
        default=None, description="The multiplier of the data to arrive at whole units."
    )
    transformation: str | None = Field(default=None, description="Transformation type.")
    source: str | None = Field(
        default=None, description="The original source of the data."
    )
    first_date: dateType | None = Field(
        default=None, description="The first date of the data."
    )
    last_date: dateType | None = Field(
        default=None, description="The last date of the data."
    )
    last_insert_timestamp: datetime | None = Field(
        default=None,
        description="The time of the last update. Data is typically reported with a lag.",
    )


class SugraAvailableIndicatorsFetcher(
    Fetcher[SugraAvailableIndicatorsQueryParams, list[SugraAvailableIndicatorsData]]
):
    """Fetch the macroeconomic indicator catalog from the Sugra API.

    Backed by /api/v1/macro/indicators/available, which fetches and cleans the
    catalog server-side (cached 7d). Fields already match the standard model -
    a direct validation.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraAvailableIndicatorsQueryParams:
        """Transform the query parameters."""
        return SugraAvailableIndicatorsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraAvailableIndicatorsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw catalog payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/macro/indicators/available", api_key, {})
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraAvailableIndicatorsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraAvailableIndicatorsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        results = (data or {}).get("results") or []
        if not results:
            raise EmptyDataError("No indicators returned.")
        return [
            SugraAvailableIndicatorsData.model_validate(r)
            for r in results
            if isinstance(r, dict) and r.get("symbol")
        ]
