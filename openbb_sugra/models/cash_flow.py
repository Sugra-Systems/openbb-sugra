"""Sugra Cash Flow Statement Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.cash_flow import (
    CashFlowStatementData,
    CashFlowStatementQueryParams,
)
from pydantic import Field


class SugraCashFlowStatementQueryParams(CashFlowStatementQueryParams):
    """Sugra Cash Flow Statement Query Parameters."""

    period: str = Field(
        default="annual",
        description="Reporting period. One of annual, quarter.",
    )


class SugraCashFlowStatementData(CashFlowStatementData):
    """Sugra Cash Flow Statement Data."""

    operating_cash_flow: float | None = Field(
        default=None, description="Net cash from operating activities."
    )
    investing_cash_flow: float | None = Field(
        default=None, description="Net cash from investing activities."
    )
    financing_cash_flow: float | None = Field(
        default=None, description="Net cash from financing activities."
    )
    free_cash_flow: float | None = Field(default=None, description="Free cash flow.")
    capital_expenditure: float | None = Field(default=None, description="Capital expenditure.")
    end_cash_position: float | None = Field(
        default=None, description="Cash position at the end of the period."
    )


class SugraCashFlowStatementFetcher(
    Fetcher[SugraCashFlowStatementQueryParams, list[SugraCashFlowStatementData]]
):
    """Fetch cash flow statements from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCashFlowStatementQueryParams:
        """Transform the query parameters."""
        return SugraCashFlowStatementQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCashFlowStatementQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw cash flow statement rows from the Sugra API."""
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
            f"/api/v2/quotes/{query.symbol.upper()}/{periodicity}/cash-flow",
            api_key,
        )
        payload = envelope_data(response)
        rows = pivot_wide_matrix(payload)
        if query.limit:
            rows = rows[: query.limit]
        return rows

    @staticmethod
    def transform_data(
        query: SugraCashFlowStatementQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCashFlowStatementData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No cash flow data returned for the symbol.")
        return [SugraCashFlowStatementData.model_validate(d) for d in data]
