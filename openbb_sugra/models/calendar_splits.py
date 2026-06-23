"""Sugra Calendar Splits Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.calendar_splits import (
    CalendarSplitsData,
    CalendarSplitsQueryParams,
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


def _parse_ratio(ratio: Any) -> tuple[float | None, float | None]:
    """Parse a 'a:b' split ratio string into (numerator, denominator).

    Sugra reports the ratio as ``old:new`` (e.g. ``1:2`` is a 2-for-1 split),
    so the new-share count is the numerator and the old-share count the
    denominator.
    """
    if not ratio:
        return None, None
    text = str(ratio).replace(" ", "")
    if ":" not in text:
        return None, None
    left, _, right = text.partition(":")
    try:
        old = float(left)
        new = float(right)
    except ValueError:
        return None, None
    return new, old


class SugraCalendarSplitsQueryParams(CalendarSplitsQueryParams):
    """Sugra Calendar Splits Query Parameters."""


class SugraCalendarSplitsData(CalendarSplitsData):
    """Sugra Calendar Splits Data."""

    name: str | None = Field(default=None, description="Name of the company.")
    split_ratio: str | None = Field(
        default=None, description="The split ratio as reported (e.g. 1:2)."
    )


class SugraCalendarSplitsFetcher(
    Fetcher[SugraCalendarSplitsQueryParams, list[SugraCalendarSplitsData]]
):
    """Fetch the upcoming stock-split calendar from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCalendarSplitsQueryParams:
        """Transform the query parameters."""
        return SugraCalendarSplitsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCalendarSplitsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw split calendar from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["start"] = query.start_date.strftime("%Y-%m-%d")
        if query.end_date:
            params["end"] = query.end_date.strftime("%Y-%m-%d")
        response = await sugra_get("/api/v2/market/calendar/splits", api_key, params)
        payload = envelope_data(response)
        if isinstance(payload, dict):
            return payload.get("rows", []) or []
        return payload if isinstance(payload, list) else []

    @staticmethod
    def transform_data(
        query: SugraCalendarSplitsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCalendarSplitsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No split calendar entries returned.")

        out: list[SugraCalendarSplitsData] = []
        for r in data:
            exec_date = _parse_us_date(r.get("execution_date"))
            numerator, denominator = _parse_ratio(r.get("ratio"))
            if exec_date is None or numerator is None or denominator is None:
                continue
            out.append(
                SugraCalendarSplitsData(
                    date=exec_date,
                    symbol=r.get("symbol"),
                    numerator=numerator,
                    denominator=denominator,
                    name=r.get("company_name"),
                    split_ratio=str(r.get("ratio")).replace(" ", "") if r.get("ratio") else None,
                )
            )
        if not out:
            raise EmptyDataError("No split calendar entries returned.")
        return out
