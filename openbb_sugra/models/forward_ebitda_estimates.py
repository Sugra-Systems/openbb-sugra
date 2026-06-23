"""Sugra Forward EBITDA Estimates Model.

PROVENANCE: unlike ForwardEpsEstimates / ForwardSalesEstimates - which map
Sugra's analyst-consensus ``forward-estimates`` feed - forward EBITDA is not
carried on that consensus feed. This model maps Sugra's own forward EBITDA
*projection* from ``/api/v1/estimates/{symbol}/model``: a damped-log-trend
extrapolation of reported fundamentals, NOT an analyst consensus. ``mean`` is the
point projection and ``low_estimate`` / ``high_estimate`` are the model's
confidence band. ``number_of_analysts`` and ``standard_deviation`` are left null
to signal the non-consensus, model-derived source.
"""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.forward_ebitda_estimates import (
    ForwardEbitdaEstimatesData,
    ForwardEbitdaEstimatesQueryParams,
)


class SugraForwardEbitdaEstimatesQueryParams(ForwardEbitdaEstimatesQueryParams):
    """Sugra Forward EBITDA Estimates Query Parameters."""


class SugraForwardEbitdaEstimatesData(ForwardEbitdaEstimatesData):
    """Sugra Forward EBITDA Estimates Data (model projection, not consensus)."""


class SugraForwardEbitdaEstimatesFetcher(
    Fetcher[
        SugraForwardEbitdaEstimatesQueryParams,
        list[SugraForwardEbitdaEstimatesData],
    ]
):
    """Fetch the forward EBITDA projection from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraForwardEbitdaEstimatesQueryParams:
        """Transform the query parameters."""
        return SugraForwardEbitdaEstimatesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraForwardEbitdaEstimatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw forward-EBITDA model payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        if not query.symbol:
            raise ValueError("Symbol is required for forward EBITDA estimates.")
        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v1/estimates/{query.symbol.upper()}/model", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraForwardEbitdaEstimatesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraForwardEbitdaEstimatesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        estimates = data.get("estimates") if isinstance(data, dict) else None
        ebitda = (estimates or {}).get("ebitda") or {}
        periods = ebitda.get("periods") or []
        if not periods or ebitda.get("available") is False:
            raise EmptyDataError("No forward EBITDA estimates returned for the symbol.")

        symbol = (data.get("symbol") or query.symbol or "").upper()
        name = data.get("company_name")
        out: list[SugraForwardEbitdaEstimatesData] = []
        for period in periods:
            band = period.get("band") or {}
            point = period.get("point")
            if point is None:
                continue
            out.append(
                SugraForwardEbitdaEstimatesData(
                    symbol=symbol,
                    name=name,
                    fiscal_year=period.get("fiscal_year"),
                    mean=point,
                    low_estimate=band.get("low"),
                    high_estimate=band.get("high"),
                )
            )
        if not out:
            raise EmptyDataError("No forward EBITDA estimates returned for the symbol.")
        return out
