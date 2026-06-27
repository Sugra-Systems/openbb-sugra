"""Sugra Balance Sheet Growth Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.balance_sheet_growth import (
    BalanceSheetGrowthData,
    BalanceSheetGrowthQueryParams,
)
from pydantic import Field

# Base line-items the shipped SugraBalanceSheetFetcher curates, mapped to the
# growth_* field that carries their period-over-period change. Names mirror
# FMPBalanceSheetGrowthData where it declares an equivalent (growth_total_assets,
# growth_cash_and_cash_equivalents); the remaining curated items keep the Sugra
# base name under the same growth_ + base-name convention.
_BASE_GROWTH_FIELDS: dict[str, str] = {
    "total_assets": "growth_total_assets",
    "total_liabilities_net_minority_interest": (
        "growth_total_liabilities_net_minority_interest"
    ),
    "total_equity_gross_minority_interest": (
        "growth_total_equity_gross_minority_interest"
    ),
    "cash_and_cash_equivalents": "growth_cash_and_cash_equivalents",
}

_PERCENT = {"x-unit_measurement": "percent", "x-frontend_multiply": 100}


class SugraBalanceSheetGrowthQueryParams(BalanceSheetGrowthQueryParams):
    """Sugra Balance Sheet Growth Query Parameters."""

    period: str = Field(
        default="annual",
        description="Reporting period. One of annual, quarter.",
    )


class SugraBalanceSheetGrowthData(BalanceSheetGrowthData):
    """Sugra Balance Sheet Growth Data.

    Period-over-period growth derived from the Sugra balance sheet. Each growth
    field is a fraction (0.05 == +5%); the x-frontend_multiply:100 hint tells the
    frontend to render it as a percent.
    """

    symbol: str | None = Field(default=None, description="The ticker symbol.")
    growth_total_assets: float | None = Field(
        default=None,
        description="Growth rate of total assets.",
        json_schema_extra=_PERCENT,
    )
    growth_total_liabilities_net_minority_interest: float | None = Field(
        default=None,
        description="Growth rate of total liabilities net of minority interest.",
        json_schema_extra=_PERCENT,
    )
    growth_total_equity_gross_minority_interest: float | None = Field(
        default=None,
        description="Growth rate of total equity gross of minority interest.",
        json_schema_extra=_PERCENT,
    )
    growth_cash_and_cash_equivalents: float | None = Field(
        default=None,
        description="Growth rate of cash and cash equivalents.",
        json_schema_extra=_PERCENT,
    )


class SugraBalanceSheetGrowthFetcher(
    Fetcher[SugraBalanceSheetGrowthQueryParams, list[SugraBalanceSheetGrowthData]]
):
    """Derive balance sheet growth from the Sugra balance sheet (no new HTTP)."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraBalanceSheetGrowthQueryParams:
        """Transform the query parameters."""
        return SugraBalanceSheetGrowthQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraBalanceSheetGrowthQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return per-period base balance sheet rows from the Sugra API.

        Derived model: reuse the shipped balance sheet fetcher rather than call a
        new endpoint. ``limit`` is intentionally NOT forwarded so every available
        period is present for the growth derivation (it is applied to the final
        growth rows in ``transform_data``).
        """
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models.balance_sheet import SugraBalanceSheetFetcher

        base_query = SugraBalanceSheetFetcher.transform_query(
            {"symbol": query.symbol, "period": query.period}
        )
        raw = await SugraBalanceSheetFetcher.aextract_data(base_query, credentials)
        rows = SugraBalanceSheetFetcher.transform_data(base_query, raw)
        return [row.model_dump() for row in rows]

    @staticmethod
    def transform_data(
        query: SugraBalanceSheetGrowthQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraBalanceSheetGrowthData]:
        """Compute period-over-period growth for each curated base line-item."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No balance sheet data returned for the symbol.")

        # Oldest first so each row is compared against the immediately prior period.
        ordered = sorted(data, key=lambda row: row.get("period_ending"))

        results: list[SugraBalanceSheetGrowthData] = []
        for index in range(1, len(ordered)):
            current = ordered[index]
            prior = ordered[index - 1]
            growth: dict[str, Any] = {
                "period_ending": current.get("period_ending"),
                "fiscal_period": current.get("fiscal_period"),
                "fiscal_year": current.get("fiscal_year"),
                "symbol": query.symbol.upper(),
            }
            for base_field, growth_field in _BASE_GROWTH_FIELDS.items():
                cur_value = current.get(base_field)
                prior_value = prior.get(base_field)
                if cur_value is None or prior_value in (None, 0):
                    continue
                # Stored as a fraction; x-frontend_multiply:100 renders the percent.
                growth[growth_field] = (cur_value - prior_value) / prior_value
            results.append(SugraBalanceSheetGrowthData.model_validate(growth))

        if not results:
            raise EmptyDataError("Not enough periods to derive balance sheet growth.")

        # Present newest period first, then honour the requested limit.
        results.reverse()
        if query.limit:
            results = results[: query.limit]
        return results
