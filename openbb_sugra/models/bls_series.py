"""Sugra BLS Series Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.bls_series import (
    SeriesData,
    SeriesQueryParams,
)


def _to_iso_date(raw: str) -> str | None:
    """Normalise a BLS period to an ISO date string.

    Sugra returns monthly periods as ``YYYY-MM`` and yearly as ``YYYY``; the
    standard model's ``date`` field needs a full ISO date, so anchor partial
    periods to the first day. Full dates pass through unchanged.
    """
    raw = (raw or "").strip()
    head = raw[:4]
    if len(raw) == 4 and head.isascii() and head.isdigit():
        return f"{raw}-01-01"
    if len(raw) == 7 and head.isascii() and head.isdigit() and raw[5:7].isdigit():
        return f"{raw}-01"
    return raw or None


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

        if not rows:
            raise EmptyDataError("No BLS observations matched the query.")
        return rows
