"""Sugra Calendar Earnings Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.calendar_earnings import (
    CalendarEarningsData,
    CalendarEarningsQueryParams,
)
from pydantic import Field


def _parse_date(value: Any) -> dateType | None:
    """Parse a YYYY-MM-DD (or M/D/YYYY) date string into a date."""
    # pylint: disable=import-outside-toplevel
    from datetime import datetime

    if not value:
        return None
    if isinstance(value, dateType):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_money(value: Any) -> float | None:
    """Parse '$5.91', '($0.14)', '$78,449,129,238' or 'N/A' into a float or None."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() == "N/A":
        return None
    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.strip("()").replace("$", "").replace(",", "").strip()
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return -number if negative else number


def _parse_int(value: Any) -> int | None:
    """Parse a count string like '9' into an int, or None."""
    if value in (None, "", "N/A"):
        return None
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


class SugraCalendarEarningsQueryParams(CalendarEarningsQueryParams):
    """Sugra Calendar Earnings Query Parameters."""


class SugraCalendarEarningsData(CalendarEarningsData):
    """Sugra Calendar Earnings Data."""

    report_time: str | None = Field(
        default=None, description="Reported time relative to market hours."
    )
    num_estimates: int | None = Field(
        default=None, description="Number of analyst estimates behind the consensus."
    )
    market_cap: int | None = Field(
        default=None, description="Market capitalization at the time of the report."
    )
    fiscal_quarter_ending: str | None = Field(
        default=None, description="Fiscal quarter the report covers (e.g. May/2026)."
    )


class SugraCalendarEarningsFetcher(
    Fetcher[SugraCalendarEarningsQueryParams, list[SugraCalendarEarningsData]]
):
    """Fetch the upcoming earnings calendar from the Sugra API.

    The upstream serves a fixed forward window (about one week); start_date /
    end_date filter the returned rows client-side.
    """

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCalendarEarningsQueryParams:
        """Transform the query parameters."""
        return SugraCalendarEarningsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCalendarEarningsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw earnings calendar from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["start"] = query.start_date.strftime("%Y-%m-%d")
        if query.end_date:
            params["end"] = query.end_date.strftime("%Y-%m-%d")
        response = await sugra_get("/api/v2/market/calendar/earnings", api_key, params)
        payload = envelope_data(response)
        if isinstance(payload, dict):
            return payload.get("rows", []) or []
        return payload if isinstance(payload, list) else []

    @staticmethod
    def transform_data(
        query: SugraCalendarEarningsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCalendarEarningsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        out: list[SugraCalendarEarningsData] = []
        for record in data:
            report_date = _parse_date(record.get("report_date"))
            symbol = record.get("symbol")
            if report_date is None or not symbol:
                continue
            if query.start_date and report_date < query.start_date:
                continue
            if query.end_date and report_date > query.end_date:
                continue
            market_cap = _parse_money(record.get("market_cap"))
            out.append(
                SugraCalendarEarningsData(
                    report_date=report_date,
                    symbol=symbol,
                    name=record.get("company_name"),
                    eps_consensus=_parse_money(record.get("eps_forecast")),
                    eps_previous=_parse_money(record.get("last_year_eps")),
                    report_time=record.get("report_time"),
                    num_estimates=_parse_int(record.get("num_estimates")),
                    market_cap=int(market_cap) if market_cap is not None else None,
                    fiscal_quarter_ending=record.get("fiscal_quarter_ending"),
                )
            )
        if not out:
            raise EmptyDataError("No earnings calendar entries returned.")
        return out
