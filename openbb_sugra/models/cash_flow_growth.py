"""Sugra Cash Flow Statement Growth Model.

Derived model: there is no dedicated upstream growth endpoint. The period-over-
period growth rates are computed from the Sugra cash flow statement
(``SugraCashFlowStatementFetcher``) so the figures stay consistent with the
statement surface. Each growth value is the fractional change
``(current - prior) / prior`` (signed prior, matching the income/balance growth
models and the FMP convention the field names mirror) and is stored as a
fraction; the standard model marks these fields ``x-frontend_multiply: 100`` for
percent display.
"""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.cash_flow_growth import (
    CashFlowStatementGrowthData,
    CashFlowStatementGrowthQueryParams,
)
from openbb_core.provider.utils.descriptions import DATA_DESCRIPTIONS
from pydantic import Field

# Map each growth field (FMP-compatible name) to the source statement concept
# (snake_cased upstream concept) it is derived from. Source fields absent from a
# given symbol's statement simply leave the growth field as None.
_DERIVE_MAP: dict[str, str] = {
    "growth_net_income": "net_income_from_continuing_operations",
    "growth_depreciation_and_amortization": "depreciation_and_amortization",
    "growth_deferred_income_tax": "deferred_income_tax",
    "growth_stock_based_compensation": "stock_based_compensation",
    "growth_change_in_working_capital": "change_in_working_capital",
    "growth_inventory": "change_in_inventory",
    "growth_account_payable": "change_in_account_payable",
    "growth_account_receivables": "changes_in_account_receivables",
    "growth_other_non_cash_items": "other_non_cash_items",
    "growth_net_cash_from_operating_activities": "operating_cash_flow",
    "growth_operating_cash_flow": "operating_cash_flow",
    "growth_purchase_of_property_plant_and_equipment": "purchase_of_p_p_e",
    "growth_net_cash_from_investing_activities": "investing_cash_flow",
    "growth_repayment_of_debt": "repayment_of_debt",
    "growth_net_cash_from_financing_activities": "financing_cash_flow",
    "growth_net_change_in_cash_and_equivalents": "changes_in_cash",
    "growth_cash_at_beginning_of_period": "beginning_cash_position",
    "growth_cash_at_end_of_period": "end_cash_position",
    "growth_capital_expenditure": "capital_expenditure",
    "growth_free_cash_flow": "free_cash_flow",
}

_PCT = {"x-unit_measurement": "percent", "x-frontend_multiply": 100}


class SugraCashFlowStatementGrowthQueryParams(CashFlowStatementGrowthQueryParams):
    """Sugra Cash Flow Statement Growth Query Parameters."""

    period: str = Field(
        default="annual",
        description="Reporting period. One of annual, quarter.",
    )


class SugraCashFlowStatementGrowthData(CashFlowStatementGrowthData):
    """Sugra Cash Flow Statement Growth Data.

    Growth values are fractions (``0.15`` == 15%); the frontend multiplies by 100.
    """

    symbol: str | None = Field(default=None, description=DATA_DESCRIPTIONS.get("symbol", ""))
    growth_net_income: float | None = Field(
        default=None, description="Growth rate of net income.", json_schema_extra=_PCT
    )
    growth_depreciation_and_amortization: float | None = Field(
        default=None,
        description="Growth rate of depreciation and amortization.",
        json_schema_extra=_PCT,
    )
    growth_deferred_income_tax: float | None = Field(
        default=None,
        description="Growth rate of deferred income tax.",
        json_schema_extra=_PCT,
    )
    growth_stock_based_compensation: float | None = Field(
        default=None,
        description="Growth rate of stock-based compensation.",
        json_schema_extra=_PCT,
    )
    growth_change_in_working_capital: float | None = Field(
        default=None,
        description="Growth rate of change in working capital.",
        json_schema_extra=_PCT,
    )
    growth_account_receivables: float | None = Field(
        default=None,
        description="Growth rate of accounts receivables.",
        json_schema_extra=_PCT,
    )
    growth_inventory: float | None = Field(
        default=None, description="Growth rate of inventory.", json_schema_extra=_PCT
    )
    growth_account_payable: float | None = Field(
        default=None,
        description="Growth rate of account payable.",
        json_schema_extra=_PCT,
    )
    growth_other_non_cash_items: float | None = Field(
        default=None,
        description="Growth rate of other non-cash items.",
        json_schema_extra=_PCT,
    )
    growth_net_cash_from_operating_activities: float | None = Field(
        default=None,
        description="Growth rate of net cash provided by operating activities.",
        json_schema_extra=_PCT,
    )
    growth_purchase_of_property_plant_and_equipment: float | None = Field(
        default=None,
        description="Growth rate of investments in property, plant, and equipment.",
        json_schema_extra=_PCT,
    )
    growth_net_cash_from_investing_activities: float | None = Field(
        default=None,
        description="Growth rate of net cash used for investing activities.",
        json_schema_extra=_PCT,
    )
    growth_repayment_of_debt: float | None = Field(
        default=None,
        description="Growth rate of debt repayment.",
        json_schema_extra=_PCT,
    )
    growth_net_cash_from_financing_activities: float | None = Field(
        default=None,
        description="Growth rate of net cash used/provided by financing activities.",
        json_schema_extra=_PCT,
    )
    growth_net_change_in_cash_and_equivalents: float | None = Field(
        default=None,
        description="Growth rate of net change in cash.",
        json_schema_extra=_PCT,
    )
    growth_cash_at_beginning_of_period: float | None = Field(
        default=None,
        description="Growth rate of cash at the beginning of the period.",
        json_schema_extra=_PCT,
    )
    growth_cash_at_end_of_period: float | None = Field(
        default=None,
        description="Growth rate of cash at the end of the period.",
        json_schema_extra=_PCT,
    )
    growth_operating_cash_flow: float | None = Field(
        default=None,
        description="Growth rate of operating cash flow.",
        json_schema_extra=_PCT,
    )
    growth_capital_expenditure: float | None = Field(
        default=None,
        description="Growth rate of capital expenditure.",
        json_schema_extra=_PCT,
    )
    growth_free_cash_flow: float | None = Field(
        default=None,
        description="Growth rate of free cash flow.",
        json_schema_extra=_PCT,
    )


def _growth(current: Any, prior: Any) -> float | None:
    """Fractional period-over-period change, or None when undefined."""
    if current is None or prior is None:
        return None
    try:
        prior_f = float(prior)
        if prior_f == 0:
            return None
        return (float(current) - prior_f) / prior_f
    except (TypeError, ValueError):
        return None


class SugraCashFlowStatementGrowthFetcher(
    Fetcher[
        SugraCashFlowStatementGrowthQueryParams,
        list[SugraCashFlowStatementGrowthData],
    ]
):
    """Derive cash flow statement growth rates from the Sugra cash flow surface."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCashFlowStatementGrowthQueryParams:
        """Transform the query parameters."""
        return SugraCashFlowStatementGrowthQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCashFlowStatementGrowthQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Fetch the backing cash flow statement rows (newest period first)."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models.cash_flow import SugraCashFlowStatementFetcher

        # Need one extra period to compute growth for the oldest requested period.
        source_limit = query.limit + 1 if query.limit else None
        source_query = SugraCashFlowStatementFetcher.transform_query(
            {"symbol": query.symbol, "period": query.period, "limit": source_limit}
        )
        return await SugraCashFlowStatementFetcher.aextract_data(
            source_query, credentials, **kwargs
        )

    @staticmethod
    def transform_data(
        query: SugraCashFlowStatementGrowthQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCashFlowStatementGrowthData]:
        """Compute period-over-period growth and validate into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No cash flow data returned for the symbol.")

        # Rows arrive newest first; sort defensively so a change in upstream
        # ordering cannot silently flip signs / mispair periods. row[i] is then
        # the current period, row[i + 1] the prior.
        data = sorted(data, key=lambda r: str(r.get("period_ending") or ""), reverse=True)
        rows: list[dict] = []
        for i in range(len(data) - 1):
            current, prior = data[i], data[i + 1]
            row: dict[str, Any] = {
                "symbol": query.symbol,
                "period_ending": current.get("period_ending"),
                "fiscal_year": current.get("fiscal_year"),
                "fiscal_period": current.get("fiscal_period"),
            }
            for growth_field, source_field in _DERIVE_MAP.items():
                row[growth_field] = _growth(
                    current.get(source_field), prior.get(source_field)
                )
            rows.append(row)

        if query.limit:
            rows = rows[: query.limit]

        if not rows:
            raise EmptyDataError(
                "Insufficient periods to compute cash flow statement growth."
            )
        return [SugraCashFlowStatementGrowthData.model_validate(r) for r in rows]
