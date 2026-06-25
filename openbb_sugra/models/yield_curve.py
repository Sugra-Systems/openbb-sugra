"""Sugra Yield Curve Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.yield_curve import (
    YieldCurveData,
    YieldCurveQueryParams,
)
from pydantic import Field


class SugraYieldCurveQueryParams(YieldCurveQueryParams):
    """Sugra Yield Curve Query Parameters."""

    rating: str = Field(
        default="aaa",
        description="Bond rating: 'aaa' or 'all_ratings'.",
    )
    yield_curve_type: str = Field(
        default="spot_rate",
        description="Curve type: 'spot_rate', 'instantaneous_forward', or 'par_yield'.",
    )


class SugraYieldCurveData(YieldCurveData):
    """Sugra Yield Curve Data.

    The standard model carries only ``date`` and ``maturity`` (plus the computed
    ``maturity_years``); the rate is a provider field, added here.
    """

    rate: float | None = Field(
        default=None,
        description="Yield rate, as a decimal fraction.",
    )


class SugraYieldCurveFetcher(
    Fetcher[SugraYieldCurveQueryParams, list[SugraYieldCurveData]]
):
    """Fetch the ECB euro area government bond yield curve from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraYieldCurveQueryParams:
        """Transform the query parameters."""
        return SugraYieldCurveQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraYieldCurveQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the yield curve payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {
            "rating": query.rating,
            "yield_curve_type": query.yield_curve_type,
        }
        # The Sugra endpoint resolves the latest available date when omitted, so
        # only forward an explicit date.
        if query.date is not None:
            params["date"] = str(query.date)
        response = await sugra_get("/api/v1/ecb/yield-curve", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraYieldCurveQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraYieldCurveData]:
        """Validate the per-maturity rows (maturity is already 'year_N'/'month_N')."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        rows = (data or {}).get("rates") or []
        if not rows:
            raise EmptyDataError("No ECB yield curve data returned.")
        out: list[SugraYieldCurveData] = []
        for row in rows:
            if not isinstance(row, dict) or not row.get("maturity"):
                continue
            out.append(SugraYieldCurveData.model_validate({
                "date": row.get("date"),
                "maturity": row["maturity"],
                "rate": row.get("rate"),
            }))
        if not out:
            raise EmptyDataError("No ECB yield curve rows produced.")
        return out
