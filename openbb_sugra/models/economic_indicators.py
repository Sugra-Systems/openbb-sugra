"""Sugra Economic Indicators Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.economic_indicators import (
    EconomicIndicatorsData,
    EconomicIndicatorsQueryParams,
)
from pydantic import Field


class SugraEconomicIndicatorsQueryParams(EconomicIndicatorsQueryParams):
    """Sugra Economic Indicators Query Parameters."""

    __json_schema_extra__ = {
        "symbol": {"multiple_items_allowed": True},
        "country": {"multiple_items_allowed": True},
        "transform": {"choices": ["toya", "tpop", "tusd", "tpgp"]},
    }

    transform: str | None = Field(
        default=None,
        description="Transformation to apply: toya (YoY %), tpop (period-over-period %), "
        "tusd (USD level), tpgp (% of GDP). Default is the native level.",
    )
    frequency: str | None = Field(
        default=None,
        description="Reporting frequency. Note: this provider returns each series at "
        "its native frequency and does not resample to this value.",
    )


class SugraEconomicIndicatorsData(EconomicIndicatorsData):
    """Sugra Economic Indicators Data."""


class SugraEconomicIndicatorsFetcher(
    Fetcher[SugraEconomicIndicatorsQueryParams, list[SugraEconomicIndicatorsData]]
):
    """Fetch macroeconomic indicator series from the Sugra API.

    Backed by /api/v1/macro/indicators, which resolves each symbol-root x country
    to its series server-side (one upstream call per series, cached 24h). Percent
    series are normalized to fractions; levels are kept in their native scale.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEconomicIndicatorsQueryParams:
        """Transform the query parameters."""
        return SugraEconomicIndicatorsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEconomicIndicatorsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw indicators payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {"symbol": query.symbol}
        if query.country:
            params["country"] = query.country
        if query.transform:
            params["transform"] = query.transform
        if query.start_date:
            params["start_date"] = str(query.start_date)
        if query.end_date:
            params["end_date"] = str(query.end_date)
        response = await sugra_get("/api/v1/macro/indicators", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraEconomicIndicatorsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraEconomicIndicatorsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        results = (data or {}).get("results") or []
        if not results:
            raise EmptyDataError("No economic indicator data returned.")
        return [
            SugraEconomicIndicatorsData.model_validate(r)
            for r in results
            if isinstance(r, dict)
        ]
