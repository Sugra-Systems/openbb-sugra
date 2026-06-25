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
        response = await sugra_get(f"/api/v1/fama-french/dataset/{dataset_key}", api_key)
        payload = envelope_data(response)
        return payload.get("records", []) if isinstance(payload, dict) else []

    @staticmethod
    def transform_data(
        query: FamaFrenchFactorsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FamaFrenchFactorsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No Fama-French factor records returned.")

        start = str(query.start_date) if query.start_date else None
        end = str(query.end_date) if query.end_date else None

        rows: list[FamaFrenchFactorsData] = []
        for rec in data:
            if not isinstance(rec, dict) or rec.get("date") is None:
                continue
            record = dict(rec)
            iso = _to_iso_date(str(record.pop("date")))
            if (start and iso < start) or (end and iso > end):
                continue
            record["date"] = iso
            rows.append(FamaFrenchFactorsData.model_validate(record))

        if not rows:
            raise EmptyDataError("No Fama-French factor records matched the query.")
        return rows
