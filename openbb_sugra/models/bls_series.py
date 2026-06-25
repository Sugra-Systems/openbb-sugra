"""Sugra BLS Series Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.bls_series import (
    SeriesData,
    SeriesQueryParams,
)


def _to_iso_date(raw: str) -> str | None:
    """Normalise a BLS period to an ISO date string, or None if unparseable.

    BLS periods arrive as ``YYYY`` (annual), ``YYYY-MM`` (monthly), or
    ``YYYY-Q0N`` (quarterly, e.g. the productivity series). Partial periods are
    anchored to the first day of the period; a quarter maps to the first month
    of that quarter (Q1->01, Q2->04, Q3->07, Q4->10). An out-of-range month or
    quarter, or any other shape, returns None so the row is skipped rather than
    crashing the whole series in pydantic validation.
    """
    raw = (raw or "").strip()
    head = raw[:4]
    if not (head.isascii() and head.isdigit()):
        return None
    # Annual: YYYY
    if len(raw) == 4:
        return f"{raw}-01-01"
    # Quarterly: YYYY-Q0N / YYYY-QN
    if "Q" in raw.upper():
        qpart = raw.upper().split("Q", 1)[1].strip()
        if qpart.isascii() and qpart.isdigit() and 1 <= int(qpart) <= 4:
            return f"{head}-{(int(qpart) - 1) * 3 + 1:02d}-01"
        return None
    # Monthly: YYYY-MM
    if len(raw) == 7 and raw[5:7].isdigit() and 1 <= int(raw[5:7]) <= 12:
        return f"{raw}-01"
    return None


class SugraBlsSeriesQueryParams(SeriesQueryParams):
    """Sugra BLS Series Query Parameters."""


class SugraBlsSeriesData(SeriesData):
    """Sugra BLS Series Data."""


class SugraBlsSeriesFetcher(Fetcher[SugraBlsSeriesQueryParams, list[SugraBlsSeriesData]]):
    """Fetch a BLS economic series from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraBlsSeriesQueryParams:
        """Transform the query parameters."""
        return SugraBlsSeriesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraBlsSeriesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw BLS series payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        # Sugra keys BLS series by the lower-case catalog key (e.g. "cpi-all").
        # The standard model upper-cases `symbol`, so lower it back for the path.
        series_key = query.symbol.lower()
        response = await sugra_get(f"/api/v1/worldbank/bls/{series_key}", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraBlsSeriesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraBlsSeriesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError
        from pydantic import ValidationError

        observations = (data or {}).get("data") or []
        if not observations:
            raise EmptyDataError("No BLS observations returned.")

        symbol = query.symbol.lower()
        title = data.get("name")
        start = str(query.start_date) if query.start_date else None
        end = str(query.end_date) if query.end_date else None

        rows: list[SugraBlsSeriesData] = []
        for obs in observations:
            if not isinstance(obs, dict) or obs.get("date") is None:
                continue
            iso = _to_iso_date(str(obs["date"]))
            if iso is None:
                continue
            if (start and iso < start) or (end and iso > end):
                continue
            # A single unparseable observation must degrade to a skipped row,
            # not abort the whole series.
            try:
                rows.append(
                    SugraBlsSeriesData.model_validate(
                        {
                            "date": iso,
                            "symbol": symbol,
                            "title": title,
                            "value": obs.get("value"),
                        }
                    )
                )
            except ValidationError:
                continue

        if not rows:
            raise EmptyDataError("No BLS observations matched the query.")
        return rows
