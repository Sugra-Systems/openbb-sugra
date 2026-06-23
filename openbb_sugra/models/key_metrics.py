"""Sugra Key Metrics Model."""

# pylint: disable=unused-argument

import contextlib
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.key_metrics import (
    KeyMetricsData,
    KeyMetricsQueryParams,
)
from pydantic import Field

# Upstream `overview` keys whose value is a {end, val, ...} fact object.
_FACT_KEYS = (
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "eps_diluted",
    "rd_expense",
    "total_assets",
    "current_assets",
    "total_liabilities",
    "current_liabilities",
    "stockholders_equity",
    "retained_earnings",
    "cash",
    "long_term_debt",
    "goodwill",
    "inventory",
    "operating_cash_flow",
    "capex",
    "dividends_paid",
    "share_repurchases",
)


class SugraKeyMetricsQueryParams(KeyMetricsQueryParams):
    """Sugra Key Metrics Query Parameters."""


class SugraKeyMetricsData(KeyMetricsData):
    """Sugra Key Metrics Data."""

    revenue: float | None = Field(default=None, description="Total revenue.")
    net_income: float | None = Field(default=None, description="Net income.")
    eps_diluted: float | None = Field(default=None, description="Diluted earnings per share.")
    total_assets: float | None = Field(default=None, description="Total assets.")
    stockholders_equity: float | None = Field(
        default=None, description="Total stockholders equity."
    )
    operating_cash_flow: float | None = Field(default=None, description="Operating cash flow.")
    long_term_debt: float | None = Field(default=None, description="Long term debt.")


class SugraKeyMetricsFetcher(Fetcher[SugraKeyMetricsQueryParams, list[SugraKeyMetricsData]]):
    """Fetch the key financial metrics overview from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraKeyMetricsQueryParams:
        """Transform the query parameters."""
        return SugraKeyMetricsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraKeyMetricsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw overview snapshot from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v1/fundamentals/{query.symbol.upper()}/overview", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraKeyMetricsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraKeyMetricsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not isinstance(data, dict) or not any(isinstance(data.get(k), dict) for k in _FACT_KEYS):
            raise EmptyDataError("No key metrics returned for the symbol.")

        row: dict[str, Any] = {"symbol": query.symbol.upper()}
        period_ending: str | None = None
        for key in _FACT_KEYS:
            fact = data.get(key)
            if isinstance(fact, dict) and fact.get("val") is not None:
                row[key] = fact["val"]
                if period_ending is None and fact.get("end"):
                    period_ending = fact["end"]
        if period_ending:
            row["period_ending"] = period_ending
            with contextlib.suppress(ValueError, TypeError):
                row["fiscal_year"] = int(str(period_ending)[:4])
        return [SugraKeyMetricsData.model_validate(row)]
