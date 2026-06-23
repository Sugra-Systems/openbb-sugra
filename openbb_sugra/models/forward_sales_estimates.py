"""Sugra Forward Sales Estimates Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.forward_sales_estimates import (
    ForwardSalesEstimatesData,
    ForwardSalesEstimatesQueryParams,
)
from pydantic import Field


def _period_to_fiscal(period: str, today: dateType) -> dict[str, Any]:
    """Map a Sugra period code (0q, +1q, 0y, +1y) to fiscal/calendar hints."""
    year = today.year
    fp = "Q1" if period.endswith("q") else "FY"
    offset = 0
    body = period[:-1]
    if body.startswith("+"):
        offset = int(body[1:] or "0")
    elif body.lstrip("-").isdigit():
        offset = int(body)
    cal_year = year + offset if period.endswith("y") else year
    return {
        "fiscal_year": cal_year,
        "fiscal_period": fp,
        "calendar_year": cal_year,
        "calendar_period": fp,
    }


class SugraForwardSalesEstimatesQueryParams(ForwardSalesEstimatesQueryParams):
    """Sugra Forward Sales Estimates Query Parameters."""


class SugraForwardSalesEstimatesData(ForwardSalesEstimatesData):
    """Sugra Forward Sales Estimates Data."""

    period: str | None = Field(
        default=None, description="Sugra period code (e.g. 0q, +1q, 0y, +1y)."
    )
    year_ago_revenue: float | None = Field(
        default=None, description="Revenue for the same period one year ago."
    )
    growth: float | None = Field(
        default=None, description="Estimated revenue growth versus the year-ago period."
    )


class SugraForwardSalesEstimatesFetcher(
    Fetcher[
        SugraForwardSalesEstimatesQueryParams,
        list[SugraForwardSalesEstimatesData],
    ]
):
    """Fetch forward sales (revenue) estimates from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraForwardSalesEstimatesQueryParams:
        """Transform the query parameters."""
        return SugraForwardSalesEstimatesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraForwardSalesEstimatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return raw forward-estimates payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        if not query.symbol:
            raise ValueError("Symbol is required for forward sales estimates.")
        api_key = get_api_key(credentials)
        response = await sugra_get(
            f"/api/v2/quotes/{query.symbol.upper()}/forward-estimates", api_key
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraForwardSalesEstimatesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraForwardSalesEstimatesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from datetime import datetime, timezone

        from openbb_core.provider.utils.errors import EmptyDataError

        rows = data.get("revenue_estimate", []) if isinstance(data, dict) else []
        if not rows:
            raise EmptyDataError("No forward sales estimates returned for the symbol.")

        today = datetime.now(timezone.utc).date()
        symbol = (query.symbol or "").upper()
        out: list[SugraForwardSalesEstimatesData] = []
        for r in rows:
            period = r.get("period", "")
            fiscal = _period_to_fiscal(period, today)
            out.append(
                SugraForwardSalesEstimatesData(
                    symbol=symbol,
                    date=today,
                    period=period,
                    low_estimate=r.get("low"),
                    high_estimate=r.get("high"),
                    mean=r.get("avg"),
                    number_of_analysts=r.get("numberOfAnalysts"),
                    year_ago_revenue=r.get("yearAgoRevenue"),
                    growth=r.get("growth"),
                    **fiscal,
                )
            )
        return out
