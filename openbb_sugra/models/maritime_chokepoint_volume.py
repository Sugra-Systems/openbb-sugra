"""Sugra Maritime Chokepoint Volume Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.maritime_chokepoint_volume import (
    MaritimeChokePointVolumeData,
    MaritimeChokePointVolumeQueryParams,
)
from pydantic import Field


def _parse_int_date(value: Any) -> dateType | None:
    """Parse an ISO (YYYY-MM-DD) or int (YYYYMMDD) value into a date."""
    if value is None:
        return None
    text = str(value).strip()
    # ISO date, the format the Sugra endpoint actually returns.
    try:
        return dateType.fromisoformat(text[:10])
    except (ValueError, TypeError):
        pass
    if len(text) == 8 and text.isascii() and text.isdigit():
        try:
            return dateType(int(text[:4]), int(text[4:6]), int(text[6:8]))
        except (ValueError, TypeError):
            return None
    return None


class SugraMaritimeChokePointVolumeQueryParams(MaritimeChokePointVolumeQueryParams):
    """Sugra Maritime Chokepoint Volume Query Parameters."""


class SugraMaritimeChokePointVolumeData(MaritimeChokePointVolumeData):
    """Sugra Maritime Chokepoint Volume Data."""

    chokepoint_code: str | None = Field(
        default=None, description="Chokepoint ID assigned by the source."
    )
    name: str | None = Field(default=None, description="Name of the chokepoint.")
    transit_calls: int | None = Field(
        default=None, description="Total number of transit calls on the day."
    )
    transit_calls_container: int | None = Field(
        default=None, description="Number of container-vessel transit calls on the day."
    )
    capacity: float | None = Field(
        default=None, description="Estimated transiting capacity for the day."
    )


class SugraMaritimeChokePointVolumeFetcher(
    Fetcher[
        SugraMaritimeChokePointVolumeQueryParams,
        list[SugraMaritimeChokePointVolumeData],
    ]
):
    """Fetch maritime chokepoint daily transit volume from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraMaritimeChokePointVolumeQueryParams:
        """Transform the query parameters."""
        return SugraMaritimeChokePointVolumeQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraMaritimeChokePointVolumeQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw chokepoint activity rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["start"] = query.start_date.strftime("%Y-%m-%d")
        if query.end_date:
            params["end"] = query.end_date.strftime("%Y-%m-%d")
        if "start" not in params and "end" not in params:
            # The activity endpoint caps limit at 365 (one year of daily rows).
            params["limit"] = 365
        response = await sugra_get("/api/v1/maritime/chokepoints/activity", api_key, params)
        payload = envelope_data(response)
        rows = payload.get("entries", []) if isinstance(payload, dict) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraMaritimeChokePointVolumeQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraMaritimeChokePointVolumeData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No maritime chokepoint activity returned.")

        results: list[SugraMaritimeChokePointVolumeData] = []
        for item in data:
            parsed = _parse_int_date(item.get("date"))
            if parsed is None:
                continue
            code = item.get("portid")
            results.append(
                SugraMaritimeChokePointVolumeData(
                    date=parsed,
                    chokepoint_code=None if code is None else str(code),
                    name=item.get("portname"),
                    transit_calls=item.get("n_total"),
                    transit_calls_container=item.get("n_container"),
                    capacity=item.get("capacity"),
                )
            )

        if not results:
            raise EmptyDataError("No maritime chokepoint volume rows produced.")
        return results
