"""Sugra Analyst Estimates Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.analyst_estimates import (
    AnalystEstimatesData,
    AnalystEstimatesQueryParams,
)
from pydantic import Field


class SugraAnalystEstimatesQueryParams(AnalystEstimatesQueryParams):
    """Sugra Analyst Estimates Query Parameters."""


class SugraAnalystEstimatesData(AnalystEstimatesData):
    """Sugra Analyst Estimates Data."""

    period: str | None = Field(
        default=None, description="Sugra period code (e.g. 0q, +1q, 0y, +1y)."
    )


class SugraAnalystEstimatesFetcher(
    Fetcher[SugraAnalystEstimatesQueryParams, list[SugraAnalystEstimatesData]]
):
    """Fetch analyst revenue and EPS estimates from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraAnalystEstimatesQueryParams:
        """Transform the query parameters."""
        return SugraAnalystEstimatesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraAnalystEstimatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return raw forward-estimates payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(
            f"/api/v2/quotes/{query.symbol.upper()}/forward-estimates", api_key
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraAnalystEstimatesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraAnalystEstimatesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from datetime import datetime, timezone

        from openbb_core.provider.utils.errors import EmptyDataError

        earnings = data.get("earnings_estimate", []) if isinstance(data, dict) else []
        revenue = data.get("revenue_estimate", []) if isinstance(data, dict) else []
        if not earnings and not revenue:
            raise EmptyDataError("No analyst estimates returned for the symbol.")

        eps_by_period = {r.get("period"): r for r in earnings}
        rev_by_period = {r.get("period"): r for r in revenue}
        periods = list(dict.fromkeys(list(eps_by_period) + list(rev_by_period)))

        today = datetime.now(timezone.utc).date()
        symbol = query.symbol.upper()
        out: list[SugraAnalystEstimatesData] = []
        for period in periods:
            eps = eps_by_period.get(period, {})
            rev = rev_by_period.get(period, {})
            out.append(
                SugraAnalystEstimatesData(
                    symbol=symbol,
                    date=today,
                    period=period,
                    estimated_revenue_low=rev.get("low"),
                    estimated_revenue_high=rev.get("high"),
                    estimated_revenue_avg=rev.get("avg"),
                    estimated_eps_avg=eps.get("avg"),
                    estimated_eps_high=eps.get("high"),
                    estimated_eps_low=eps.get("low"),
                    number_analyst_estimated_revenue=rev.get("numberOfAnalysts"),
                    number_analysts_estimated_eps=eps.get("numberOfAnalysts"),
                )
            )
        return out
