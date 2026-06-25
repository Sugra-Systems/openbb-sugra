"""Sugra Fama-French Factors Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_famafrench.models.factors import (
    FamaFrenchFactorsData,
    FamaFrenchFactorsQueryParams,
)

# Sugra serves Ken French's US ("america") research data. Map the standard
# (factor, frequency) selection onto the Sugra catalog dataset key.
_DATASET_KEYS: dict[tuple[str, str], str] = {
    ("3_factors", "monthly"): "factors-3-monthly",
    ("3_factors", "daily"): "factors-3-daily",
    ("5_factors", "monthly"): "factors-5-monthly",
    ("5_factors", "daily"): "factors-5-daily",
    ("momentum", "monthly"): "momentum-monthly",
    ("momentum", "daily"): "momentum-daily",
    ("st_reversal", "monthly"): "st-reversal",
    ("lt_reversal", "monthly"): "lt-reversal",
}


def _to_iso_date(raw: str) -> str:
    """Normalise a Ken French period (YYYYMMDD / YYYYMM / YYYY) to ISO date."""
    raw = (raw or "").strip()
    if len(raw) == 8:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    if len(raw) == 6:
        return f"{raw[:4]}-{raw[4:6]}-01"
    if len(raw) == 4:
        return f"{raw}-12-31"
    return raw


class SugraFamaFrenchFactorsFetcher(
    Fetcher[FamaFrenchFactorsQueryParams, list[FamaFrenchFactorsData]]
):
    """Fetch Fama-French research factors (US) from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> FamaFrenchFactorsQueryParams:
        """Transform the query parameters."""
        return FamaFrenchFactorsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FamaFrenchFactorsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw factor records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        if query.region != "america":
            raise EmptyDataError(
                "Sugra serves Ken French US research data only; "
                f"region '{query.region}' is not available."
            )
        dataset_key = _DATASET_KEYS.get((query.factor, query.frequency))
        if dataset_key is None:
            raise EmptyDataError(
                f"Sugra does not serve the '{query.factor}' factor at "
                f"'{query.frequency}' frequency."
            )

        api_key = get_api_key(credentials)
        # Default response is only the trailing 60 records; request the full
        # history (the endpoint caps at 1200 - the complete monthly series back
        # to 1926, ~5y for daily) so a deep start_date is not silently truncated.
        response = await sugra_get(
            f"/api/v1/fama-french/dataset/{dataset_key}", api_key, {"limit": 1200}
        )
        payload = envelope_data(response)
        return payload.get("records", []) if isinstance(payload, dict) else []

    @staticmethod
    def transform_data(
        query: FamaFrenchFactorsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FamaFrenchFactorsData]:
        """Validate, transform, window, and order into the standard model."""
        # pylint: disable=import-outside-toplevel
        from datetime import date as _date

        from openbb_core.provider.utils.errors import EmptyDataError
        from pydantic import ValidationError

        if not data:
            raise EmptyDataError("No Fama-French factor records returned.")

        # Compare real dates, not lexical strings. Monthly records are anchored
        # to the first of the month, so clamp a mid-month start_date down to the
        # period start - otherwise the boundary month is wrongly dropped.
        start = query.start_date
        end = query.end_date
        if start and query.frequency == "monthly":
            start = start.replace(day=1)

        rows: list[FamaFrenchFactorsData] = []
        for rec in data:
            if not isinstance(rec, dict) or rec.get("date") is None:
                continue
            record = dict(rec)
            iso = _to_iso_date(str(record.pop("date")))
            try:
                period = _date.fromisoformat(iso)
            except ValueError:
                continue
            if (start and period < start) or (end and period > end):
                continue
            record["date"] = iso
            try:
                rows.append(FamaFrenchFactorsData.model_validate(record))
            except ValidationError:
                continue

        if not rows:
            raise EmptyDataError("No Fama-French factor records matched the query.")
        # The Sugra API returns newest-first; the standard model orders ascending.
        rows.sort(key=lambda r: r.date)
        return rows
