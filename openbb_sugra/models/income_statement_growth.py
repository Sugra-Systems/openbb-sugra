"""Sugra Income Statement Growth Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.income_statement_growth import (
    IncomeStatementGrowthData,
    IncomeStatementGrowthQueryParams,
)
from pydantic import Field

# Growth field -> source field on the Sugra income statement Data model. The
# source fetcher exposes these as clean snake_case attributes after validation.
# Field names mirror FMPIncomeStatementGrowthData so the obb.* columns line up
# when a caller swaps provider="fmp" <-> "sugra". NB: ``growth_basic_earings_per_share``
# carries FMP's upstream misspelling ("earings") on purpose - matching it is what
# aligns the column.
_GROWTH_FIELDS = {
    "growth_revenue": "total_revenue",
    "growth_gross_profit": "gross_profit",
    "growth_operating_income": "operating_income",
    "growth_consolidated_net_income": "net_income",
    "growth_basic_earings_per_share": "basic_eps",
    "growth_diluted_earnings_per_share": "diluted_eps",
}

_PERCENT_GROWTH = {"x-unit_measurement": "percent", "x-frontend_multiply": 100}


def _period_growth(current: float | None, previous: float | None) -> float | None:
    """Return period-over-period growth as a fraction (0.15 == +15 percent).

    Matches the upstream convention of dividing by the prior (signed) value;
    returns None when either side is missing or the prior value is zero.
    """
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / previous


class SugraIncomeStatementGrowthQueryParams(IncomeStatementGrowthQueryParams):
    """Sugra Income Statement Growth Query Parameters."""

    period: str = Field(
        default="annual",
        description="Reporting period. One of annual, quarter.",
    )


class SugraIncomeStatementGrowthData(IncomeStatementGrowthData):
    """Sugra Income Statement Growth Data.

    Growth values are stored as fractions; the percent display multiplier lives
    in each field's json_schema_extra so the frontend renders them as percents.
    """

    growth_revenue: float | None = Field(
        default=None,
        description="Growth rate of total revenue.",
        json_schema_extra=_PERCENT_GROWTH,
    )
    growth_gross_profit: float | None = Field(
        default=None,
        description="Growth rate of gross profit.",
        json_schema_extra=_PERCENT_GROWTH,
    )
    growth_operating_income: float | None = Field(
        default=None,
        description="Growth rate of operating income.",
        json_schema_extra=_PERCENT_GROWTH,
    )
    growth_consolidated_net_income: float | None = Field(
        default=None,
        description="Growth rate of consolidated net income.",
        json_schema_extra=_PERCENT_GROWTH,
    )
    growth_basic_earings_per_share: float | None = Field(
        default=None,
        description="Growth rate of basic earnings per share.",
        json_schema_extra=_PERCENT_GROWTH,
    )
    growth_diluted_earnings_per_share: float | None = Field(
        default=None,
        description="Growth rate of diluted earnings per share.",
        json_schema_extra=_PERCENT_GROWTH,
    )


class SugraIncomeStatementGrowthFetcher(
    Fetcher[
        SugraIncomeStatementGrowthQueryParams,
        list[SugraIncomeStatementGrowthData],
    ]
):
    """Derive income statement growth from Sugra income statements."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraIncomeStatementGrowthQueryParams:
        """Transform the query parameters."""
        return SugraIncomeStatementGrowthQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraIncomeStatementGrowthQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Fetch the backing income statements, newest period first.

        One extra period is requested so the oldest growth row still has a
        prior period to compare against.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.models.income_statement import (
            SugraIncomeStatementFetcher,
            SugraIncomeStatementQueryParams,
        )

        source_query = SugraIncomeStatementQueryParams(
            symbol=query.symbol,
            period=query.period,
            limit=query.limit + 1 if query.limit else None,
        )
        rows = await SugraIncomeStatementFetcher.aextract_data(
            source_query, credentials, **kwargs
        )
        statements = SugraIncomeStatementFetcher.transform_data(source_query, rows)
        return [s.model_dump() for s in statements]

    @staticmethod
    def transform_data(
        query: SugraIncomeStatementGrowthQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraIncomeStatementGrowthData]:
        """Derive period-over-period growth from consecutive statements."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No income statement data returned for the symbol.")

        # The backing fetcher returns newest period first; sort defensively so a
        # change in upstream ordering cannot silently flip signs / mispair periods.
        data = sorted(data, key=lambda r: str(r.get("period_ending") or ""), reverse=True)

        results: list[SugraIncomeStatementGrowthData] = []
        for current, previous in zip(data, data[1:]):
            row: dict[str, Any] = {
                "period_ending": current.get("period_ending"),
                "fiscal_period": current.get("fiscal_period"),
                "fiscal_year": current.get("fiscal_year"),
            }
            for growth_field, source_field in _GROWTH_FIELDS.items():
                row[growth_field] = _period_growth(
                    current.get(source_field), previous.get(source_field)
                )
            results.append(SugraIncomeStatementGrowthData.model_validate(row))

        if query.limit:
            results = results[: query.limit]
        if not results:
            raise EmptyDataError(
                "Not enough periods to compute income statement growth."
            )
        return results
