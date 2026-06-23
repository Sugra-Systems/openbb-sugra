"""Sugra Income Statement Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.income_statement import (
    IncomeStatementData,
    IncomeStatementQueryParams,
)
from pydantic import Field


class SugraIncomeStatementQueryParams(IncomeStatementQueryParams):
    """Sugra Income Statement Query Parameters."""

    period: str = Field(
        default="annual",
        description="Reporting period. One of annual, quarter.",
    )


class SugraIncomeStatementData(IncomeStatementData):
    """Sugra Income Statement Data."""

    total_revenue: float | None = Field(default=None, description="Total revenue.")
    gross_profit: float | None = Field(default=None, description="Gross profit.")
    operating_income: float | None = Field(default=None, description="Operating income.")
    net_income: float | None = Field(default=None, description="Net income.")
    basic_eps: float | None = Field(
        default=None,
        description="Basic earnings per share.",
        validation_alias="basic_e_p_s",
    )
    diluted_eps: float | None = Field(
        default=None,
        description="Diluted earnings per share.",
        validation_alias="diluted_e_p_s",
    )


class SugraIncomeStatementFetcher(
    Fetcher[SugraIncomeStatementQueryParams, list[SugraIncomeStatementData]]
):
    """Fetch income statements from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraIncomeStatementQueryParams:
        """Transform the query parameters."""
        return SugraIncomeStatementQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraIncomeStatementQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw income statement rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import (
            envelope_data,
            get_api_key,
            pivot_wide_matrix,
            sugra_get,
        )

        api_key = get_api_key(credentials)
        periodicity = "quarter" if query.period.lower().startswith("q") else "annual"
        response = await sugra_get(
            f"/api/v2/quotes/{query.symbol.upper()}/{periodicity}/income-statement",
            api_key,
        )
        payload = envelope_data(response)
        rows = pivot_wide_matrix(payload)
        if query.limit:
            rows = rows[: query.limit]
        return rows

    @staticmethod
    def transform_data(
        query: SugraIncomeStatementQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraIncomeStatementData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No income statement data returned for the symbol.")
        return [SugraIncomeStatementData.model_validate(d) for d in data]
