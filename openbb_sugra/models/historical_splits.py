"""Sugra Historical Splits Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.historical_splits import (
    HistoricalSplitsData,
    HistoricalSplitsQueryParams,
)


def _parse_date(value: Any) -> dateType | None:
    """Parse a YYYY-MM-DD (or ISO) date string into a date."""
    # pylint: disable=import-outside-toplevel
    from datetime import datetime

    if not value:
        return None
    if isinstance(value, dateType):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _to_float(value: Any) -> float | None:
    """Coerce a value to float, or None when missing or non-numeric."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _split_ratio(numerator: float | None, denominator: float | None) -> str | None:
    """Render numerator/denominator as a 'new:old' split-ratio string (e.g. 10:1)."""
    if numerator is None or denominator is None:
        return None

    def _fmt(number: float) -> str:
        return str(int(number)) if number.is_integer() else f"{number:g}"

    return f"{_fmt(numerator)}:{_fmt(denominator)}"


class SugraHistoricalSplitsQueryParams(HistoricalSplitsQueryParams):
    """Sugra Historical Splits Query Parameters."""


class SugraHistoricalSplitsData(HistoricalSplitsData):
    """Sugra Historical Splits Data."""


class SugraHistoricalSplitsFetcher(
    Fetcher[
        SugraHistoricalSplitsQueryParams,
        list[SugraHistoricalSplitsData],
    ]
):
    """Fetch the historical stock-split series from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraHistoricalSplitsQueryParams:
        """Transform the query parameters."""
        return SugraHistoricalSplitsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraHistoricalSplitsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw historical splits from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v2/quotes/{query.symbol.upper()}/splits", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, list) else []

    @staticmethod
    def transform_data(
        query: SugraHistoricalSplitsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraHistoricalSplitsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        out: list[SugraHistoricalSplitsData] = []
        for record in data:
            split_date = _parse_date(record.get("date"))
            numerator = _to_float(record.get("numerator"))
            denominator = _to_float(record.get("denominator"))
            if split_date is None or numerator is None or denominator is None:
                continue
            out.append(
                SugraHistoricalSplitsData(
                    date=split_date,
                    numerator=numerator,
                    denominator=denominator,
                    split_ratio=_split_ratio(numerator, denominator),
                )
            )
        if not out:
            raise EmptyDataError("No historical splits returned for the symbol.")
        return out
