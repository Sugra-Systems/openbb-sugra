"""Sugra Balance Sheet Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.balance_sheet import (
    BalanceSheetData,
    BalanceSheetQueryParams,
)
from pydantic import Field


class SugraBalanceSheetQueryParams(BalanceSheetQueryParams):
    """Sugra Balance Sheet Query Parameters."""

    period: str = Field(
        default="annual",
        description="Reporting period. One of annual, quarter.",
    )


class SugraBalanceSheetData(BalanceSheetData):
    """Sugra Balance Sheet Data."""

    total_assets: float | None = Field(default=None, description="Total assets.")
    total_liabilities_net_minority_interest: float | None = Field(
        default=None, description="Total liabilities net of minority interest."
    )
    total_equity_gross_minority_interest: float | None = Field(
        default=None, description="Total equity gross of minority interest."
    )
    cash_and_cash_equivalents: float | None = Field(
        default=None, description="Cash and cash equivalents."
    )


class SugraBalanceSheetFetcher(Fetcher[SugraBalanceSheetQueryParams, list[SugraBalanceSheetData]]):
    """Fetch balance sheet statements from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraBalanceSheetQueryParams:
        """Transform the query parameters."""
        return SugraBalanceSheetQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraBalanceSheetQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw balance sheet rows from the Sugra API."""
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
            f"/api/v2/quotes/{query.symbol.upper()}/{periodicity}/balance-sheet",
            api_key,
        )
        payload = envelope_data(response)
        rows = pivot_wide_matrix(payload)
        if query.limit:
            rows = rows[: query.limit]
        return rows

    @staticmethod
    def transform_data(
        query: SugraBalanceSheetQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraBalanceSheetData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No balance sheet data returned for the symbol.")
        return [SugraBalanceSheetData.model_validate(d) for d in data]
