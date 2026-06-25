"""Sugra Fama-French Breakpoints Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_famafrench.models.breakpoints import (
    FamaFrenchBreakpointData,
    FamaFrenchBreakpointQueryParams,
)

# Breakpoint files are short (annual ratios ~100 rows, monthly ME ~1.2k rows);
# the ceiling matches the Sugra API limit (le=30000) with ample headroom.
_FULL_SERIES_LIMIT = 30000


def _breakpoint_date_to_iso(raw: str) -> str:
    """Ken French breakpoint period -> ISO. Monthly tokens (me, 2-12) anchor to
    MONTH END, annual ratio tokens to year end - matching the upstream provider's
    `to_datetime(YYYYMM) + MonthEnd(0)` / `str(YYYY) + '-12-31'` convention."""
    # pylint: disable=import-outside-toplevel
    from datetime import date, timedelta

    raw = (raw or "").strip()
    if len(raw) == 6:
        year, month = int(raw[:4]), int(raw[4:6])
        if month >= 12:
            return f"{year}-12-31"
        return (date(year, month + 1, 1) - timedelta(days=1)).isoformat()
    if len(raw) == 4:
        return f"{raw}-12-31"
    return raw


class SugraFamaFrenchBreakpointFetcher(
    Fetcher[FamaFrenchBreakpointQueryParams, list[FamaFrenchBreakpointData]]
):
    """Fetch Fama-French NYSE breakpoints from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> FamaFrenchBreakpointQueryParams:
        """Transform the query parameters."""
        return FamaFrenchBreakpointQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FamaFrenchBreakpointQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw breakpoint records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(
            "/api/v1/fama-french/breakpoints",
            api_key,
            {"breakpoint_type": query.breakpoint_type, "limit": _FULL_SERIES_LIMIT},
        )
        payload = envelope_data(response)
        return payload.get("records", []) if isinstance(payload, dict) else []

    @staticmethod
    def transform_data(
        query: FamaFrenchBreakpointQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FamaFrenchBreakpointData]:
        """Window by date and validate into the standard model."""
        # pylint: disable=import-outside-toplevel
        from datetime import date as _date

        from openbb_core.provider.utils.errors import EmptyDataError
        from pydantic import ValidationError

        if not data:
            raise EmptyDataError("No Fama-French breakpoint records returned.")

        start = query.start_date
        end = query.end_date

        rows: list[FamaFrenchBreakpointData] = []
        for rec in data:
            if not isinstance(rec, dict) or rec.get("date") is None:
                continue
            record = dict(rec)
            iso = _breakpoint_date_to_iso(str(record.pop("date")))
            try:
                period = _date.fromisoformat(iso)
            except ValueError:
                continue
            if (start and period < start) or (end and period > end):
                continue
            record["date"] = iso
            try:
                rows.append(FamaFrenchBreakpointData.model_validate(record))
            except ValidationError:
                continue

        if not rows:
            raise EmptyDataError("No Fama-French breakpoint records matched the query.")
        rows.sort(key=lambda r: r.date)
        return rows
