"""Sugra Financial Ratios Model."""

# pylint: disable=unused-argument

import contextlib
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.financial_ratios import (
    FinancialRatiosData,
    FinancialRatiosQueryParams,
)
from pydantic import Field


class SugraFinancialRatiosQueryParams(FinancialRatiosQueryParams):
    """Sugra Financial Ratios Query Parameters."""


class SugraFinancialRatiosData(FinancialRatiosData):
    """Sugra Financial Ratios Data."""

    gross_margin: float | None = Field(default=None, description="Gross margin.")
    operating_margin: float | None = Field(default=None, description="Operating margin.")
    net_margin: float | None = Field(default=None, description="Net profit margin.")
    return_on_equity: float | None = Field(default=None, description="Return on equity.")
    return_on_assets: float | None = Field(default=None, description="Return on assets.")
    debt_to_equity: float | None = Field(default=None, description="Debt to equity ratio.")
    current_ratio: float | None = Field(default=None, description="Current ratio.")
    quick_ratio: float | None = Field(default=None, description="Quick ratio.")
    book_value_per_share: float | None = Field(default=None, description="Book value per share.")


class SugraFinancialRatiosFetcher(
    Fetcher[SugraFinancialRatiosQueryParams, list[SugraFinancialRatiosData]]
):
    """Fetch aggregated financial ratios from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraFinancialRatiosQueryParams:
        """Transform the query parameters."""
        return SugraFinancialRatiosQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraFinancialRatiosQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw ratios snapshot from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v1/fundamentals/{query.symbol.upper()}/ratios", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraFinancialRatiosQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraFinancialRatiosData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        ratios = (data or {}).get("ratios") if isinstance(data, dict) else None
        if not ratios:
            raise EmptyDataError("No financial ratios returned for the symbol.")
        row: dict[str, Any] = {
            "symbol": data.get("ticker") or query.symbol.upper(),
            "period_ending": data.get("as_of"),
        }
        as_of = data.get("as_of")
        if as_of:
            with contextlib.suppress(ValueError, TypeError):
                row["fiscal_year"] = int(str(as_of)[:4])
        row.update({k: v for k, v in ratios.items() if v is not None})
        return [SugraFinancialRatiosData.model_validate(row)]
