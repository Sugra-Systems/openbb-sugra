"""Sugra Calendar Dividend Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.calendar_dividend import (
    CalendarDividendData,
    CalendarDividendQueryParams,
)
from pydantic import Field


def _parse_us_date(value: Any) -> dateType | None:
    """Parse an M/D/YYYY (or YYYY-MM-DD) string into a date."""
    # pylint: disable=import-outside-toplevel
    from datetime import datetime

    if not value:
        return None
    if isinstance(value, dateType):
        return value
    text = str(value).strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


class SugraCalendarDividendQueryParams(CalendarDividendQueryParams):
    """Sugra Calendar Dividend Query Parameters."""


class SugraCalendarDividendData(CalendarDividendData):
    """Sugra Calendar Dividend Data."""

    annualized_amount: float | None = Field(default=None, description="Annualized dividend amount.")


class SugraCalendarDividendFetcher(
    Fetcher[SugraCalendarDividendQueryParams, list[SugraCalendarDividendData]]
):
    """Fetch the upcoming dividend calendar from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCalendarDividendQueryParams:
        """Transform the query parameters."""
        return SugraCalendarDividendQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCalendarDividendQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw dividend calendar from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["start"] = query.start_date.strftime("%Y-%m-%d")
        if query.end_date:
            params["end"] = query.end_date.strftime("%Y-%m-%d")
        response = await sugra_get("/api/v2/market/calendar/dividends", api_key, params)
        payload = envelope_data(response)
        if isinstance(payload, dict):
            return payload.get("rows", []) or []
        return payload if isinstance(payload, list) else []

    @staticmethod
    def transform_data(
        query: SugraCalendarDividendQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCalendarDividendData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No dividend calendar entries returned.")

        out: list[SugraCalendarDividendData] = []
        for r in data:
            ex_date = _parse_us_date(r.get("ex_dividend_date"))
            if ex_date is None:
                continue
            out.append(
                SugraCalendarDividendData(
                    ex_dividend_date=ex_date,
                    symbol=r.get("symbol"),
                    amount=r.get("dividend_rate"),
                    name=r.get("company_name"),
                    record_date=_parse_us_date(r.get("record_date")),
                    payment_date=_parse_us_date(r.get("payment_date")),
                    declaration_date=_parse_us_date(r.get("announcement_date")),
                    annualized_amount=r.get("annualized_dividend"),
                )
            )
        if not out:
            raise EmptyDataError("No dividend calendar entries returned.")
        return out
