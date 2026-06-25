"""Sugra Balance of Payments Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.balance_of_payments import (
    BalanceOfPaymentsQueryParams,
    ECBCountry,
    ECBDirectInvestment,
    ECBInvestmentIncome,
    ECBMain,
    ECBOtherInvestment,
    ECBPortfolioInvestment,
    ECBServices,
    ECBSummary,
)
from pydantic import Field

_QUARTER_START_MONTH = {"1": 1, "2": 4, "3": 7, "4": 10}


class SugraBalanceOfPaymentsQueryParams(BalanceOfPaymentsQueryParams):
    """Sugra Balance of Payments Query Parameters."""

    report_type: str = Field(
        default="main",
        description=(
            "Report type: main, summary, services, investment_income, "
            "direct_investment, portfolio_investment, other_investment, country."
        ),
    )
    country: str | None = Field(
        default=None,
        description="Counterpart country (required for report_type=country).",
    )
    frequency: str = Field(
        default="monthly",
        description="monthly or quarterly (only main and summary honour it).",
    )
    start_date: str | None = Field(
        default=None,
        description="Start period (YYYY-MM or YYYY-Q#).",
    )
    end_date: str | None = Field(
        default=None,
        description="End period (YYYY-MM or YYYY-Q#).",
    )


class SugraBalanceOfPaymentsData(
    ECBMain,
    ECBSummary,
    ECBServices,
    ECBInvestmentIncome,
    ECBDirectInvestment,
    ECBPortfolioInvestment,
    ECBOtherInvestment,
    ECBCountry,
):
    """Sugra Balance of Payments Data.

    Multiply-inherits every ECB report sub-class so a row of any report_type
    validates against the union of their (all-optional) fields - mirroring the
    OpenBB ECB provider.
    """


def _period_to_date(period: str) -> str | None:
    """Convert an ECB period ('2024-03', '2024-Q1', '2024') to a date string."""
    if not period:
        return None
    period = str(period)
    if "-Q" in period:
        year, _, q = period.partition("-Q")
        month = _QUARTER_START_MONTH.get(q.strip())
        if month is None:
            return None
        return f"{year}-{month:02d}-01"
    parts = period.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{int(parts[1]):02d}-01"
    return f"{period}-01-01"


class SugraBalanceOfPaymentsFetcher(
    Fetcher[SugraBalanceOfPaymentsQueryParams, list[SugraBalanceOfPaymentsData]]
):
    """Fetch the ECB euro area balance of payments from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraBalanceOfPaymentsQueryParams:
        """Transform the query parameters."""
        return SugraBalanceOfPaymentsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraBalanceOfPaymentsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the balance of payments payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {
            "report_type": query.report_type,
            "frequency": query.frequency,
        }
        if query.country:
            params["country"] = query.country
        if query.start_date:
            params["start_period"] = str(query.start_date)
        if query.end_date:
            params["end_period"] = str(query.end_date)
        response = await sugra_get("/api/v1/ecb/balance-of-payments", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraBalanceOfPaymentsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraBalanceOfPaymentsData]:
        """Validate the wide period rows, coercing the ECB period to a date."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        rows = (data or {}).get("data") or []
        if not rows:
            raise EmptyDataError("No ECB balance of payments data returned.")
        out: list[SugraBalanceOfPaymentsData] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            mapped = dict(row)
            mapped["period"] = _period_to_date(row.get("period", ""))
            out.append(SugraBalanceOfPaymentsData.model_validate(mapped))
        if not out:
            raise EmptyDataError("No ECB balance of payments rows produced.")
        return out
