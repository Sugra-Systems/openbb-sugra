"""Sugra High Quality Market Corporate Bond Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.high_quality_market import (
    HighQualityMarketCorporateBondData,
    HighQualityMarketCorporateBondQueryParams,
)
from pydantic import Field


class SugraHighQualityMarketCorporateBondQueryParams(
    HighQualityMarketCorporateBondQueryParams
):
    """Sugra High Quality Market Corporate Bond Query Parameters."""

    __json_schema_extra__ = {"date": {"multiple_items_allowed": True}}

    yield_curve: Literal["spot", "par"] = Field(
        default="spot",
        description="The yield curve type.",
        json_schema_extra={"choices": ["spot", "par"]},
    )


class SugraHighQualityMarketCorporateBondData(HighQualityMarketCorporateBondData):
    """Sugra High Quality Market Corporate Bond Data."""


class SugraHighQualityMarketCorporateBondFetcher(
    Fetcher[
        SugraHighQualityMarketCorporateBondQueryParams,
        list[SugraHighQualityMarketCorporateBondData],
    ]
):
    """Fetch the full HQM corporate-bond yield curve from the Sugra API.

    Backed by the Sugra `/api/v1/fred/corporate/hqm` endpoint, which returns the
    whole curve (every maturity point) from ONE FRED release-table call per date -
    the production-safe alternative to the ~200 single-series fetches the curve
    would otherwise require. The endpoint already stores `rate` as a decimal
    fraction, matching the standard model (x-frontend_multiply 100).
    """

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraHighQualityMarketCorporateBondQueryParams:
        """Transform the query parameters."""
        return SugraHighQualityMarketCorporateBondQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraHighQualityMarketCorporateBondQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw HQM curve payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {"yield_curve": query.yield_curve}
        if query.date:
            params["date"] = str(query.date)
        response = await sugra_get("/api/v1/fred/corporate/hqm", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraHighQualityMarketCorporateBondQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraHighQualityMarketCorporateBondData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        results = (data or {}).get("results") or []
        if not results:
            raise EmptyDataError("No HQM corporate bond curve data returned.")
        # The endpoint emits {date, maturity, rate} with rate already a decimal
        # fraction - a direct map to the standard model.
        return [
            SugraHighQualityMarketCorporateBondData.model_validate(r)
            for r in results
            if isinstance(r, dict) and r.get("date") is not None
        ]
