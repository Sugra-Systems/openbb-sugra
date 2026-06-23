"""Sugra Forward EPS Estimates Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.forward_eps_estimates import (
    ForwardEpsEstimatesData,
    ForwardEpsEstimatesQueryParams,
)
from pydantic import Field


def _period_to_fiscal(period: str, today: dateType) -> dict[str, Any]:
    """Map a Sugra period code (0q, +1q, 0y, +1y) to fiscal/calendar hints."""
    year = today.year
    if period.endswith("q"):
        fp = "Q1"
        cper = "Q1"
    else:
        fp = "FY"
        cper = "FY"
    offset = 0
    body = period[:-1]
    if body.startswith("+"):
        offset = int(body[1:] or "0")
    elif body.lstrip("-").isdigit():
        offset = int(body)
    if period.endswith("y"):
        cal_year = year + offset
        fiscal_year = cal_year
    else:
        cal_year = year
        fiscal_year = year
    return {
        "fiscal_year": fiscal_year,
        "fiscal_period": fp,
        "calendar_year": cal_year,
        "calendar_period": cper,
    }


class SugraForwardEpsEstimatesQueryParams(ForwardEpsEstimatesQueryParams):
    """Sugra Forward EPS Estimates Query Parameters."""


class SugraForwardEpsEstimatesData(ForwardEpsEstimatesData):
    """Sugra Forward EPS Estimates Data."""

    period: str | None = Field(
        default=None, description="Sugra period code (e.g. 0q, +1q, 0y, +1y)."
    )
    year_ago_eps: float | None = Field(
        default=None, description="EPS for the same period one year ago."
    )
    growth: float | None = Field(
        default=None, description="Estimated EPS growth versus the year-ago period."
    )


class SugraForwardEpsEstimatesFetcher(
    Fetcher[SugraForwardEpsEstimatesQueryParams, list[SugraForwardEpsEstimatesData]]
):
    """Fetch forward EPS estimates from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraForwardEpsEstimatesQueryParams:
        """Transform the query parameters."""
        return SugraForwardEpsEstimatesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraForwardEpsEstimatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return raw forward-estimates payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        if not query.symbol:
            raise ValueError("Symbol is required for forward EPS estimates.")
        api_key = get_api_key(credentials)
        response = await sugra_get(
            f"/api/v2/quotes/{query.symbol.upper()}/forward-estimates", api_key
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraForwardEpsEstimatesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraForwardEpsEstimatesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from datetime import datetime, timezone

        from openbb_core.provider.utils.errors import EmptyDataError

        rows = data.get("earnings_estimate", []) if isinstance(data, dict) else []
        if not rows:
            raise EmptyDataError("No forward EPS estimates returned for the symbol.")

        today = datetime.now(timezone.utc).date()
        symbol = (query.symbol or "").upper()
        out: list[SugraForwardEpsEstimatesData] = []
        for r in rows:
            period = r.get("period", "")
            fiscal = _period_to_fiscal(period, today)
            out.append(
                SugraForwardEpsEstimatesData(
                    symbol=symbol,
                    date=today,
                    period=period,
                    low_estimate=r.get("low"),
                    high_estimate=r.get("high"),
                    mean=r.get("avg"),
                    number_of_analysts=r.get("numberOfAnalysts"),
                    year_ago_eps=r.get("yearAgoEps"),
                    growth=r.get("growth"),
                    **fiscal,
                )
            )
        return out
