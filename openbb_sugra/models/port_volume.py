"""Sugra Port Volume Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.port_volume import (
    PortVolumeData,
    PortVolumeQueryParams,
)
from pydantic import Field


def _parse_date(value: Any) -> dateType | None:
    """Parse an int/str YYYYMMDD or ISO date into a date."""
    if value is None:
        return None
    text = str(value).strip()
    if len(text) == 8 and text.isascii() and text.isdigit():
        try:
            return dateType(int(text[:4]), int(text[4:6]), int(text[6:8]))
        except (ValueError, TypeError):
            return None
    # pylint: disable=import-outside-toplevel
    try:
        from dateutil import parser

        return parser.parse(text).date()
    except (ValueError, TypeError, ImportError):
        return None


class SugraPortVolumeQueryParams(PortVolumeQueryParams):
    """Sugra Port Volume Query Parameters."""

    port_id: str | None = Field(default=None, description="Filter activity to a single port id.")
    country: str | None = Field(default=None, description="Filter activity to ports in a country.")
    limit: int | None = Field(default=50, description="Maximum number of rows to return.")


class SugraPortVolumeData(PortVolumeData):
    """Sugra Port Volume Data."""

    transit_calls: int | None = Field(
        default=None, description="Total number of port calls on the day."
    )


class SugraPortVolumeFetcher(Fetcher[SugraPortVolumeQueryParams, list[SugraPortVolumeData]]):
    """Fetch port daily activity from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraPortVolumeQueryParams:
        """Transform the query parameters."""
        return SugraPortVolumeQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraPortVolumeQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw port activity rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.port_id:
            params["port_id"] = query.port_id
        if query.country:
            params["country"] = query.country
        if query.limit:
            params["limit"] = query.limit
        response = await sugra_get("/api/v1/maritime/ports/activity", api_key, params)
        payload = envelope_data(response)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("entries", "activity", "data", "records", "rows"):
                rows = payload.get(key)
                if isinstance(rows, list):
                    return rows
        return []

    @staticmethod
    def transform_data(
        query: SugraPortVolumeQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraPortVolumeData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No port activity returned.")

        results: list[SugraPortVolumeData] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            parsed = _parse_date(item.get("date"))
            if parsed is None:
                continue
            code = item.get("portid", item.get("port_id"))
            results.append(
                SugraPortVolumeData(
                    date=parsed,
                    port_code=None if code is None else str(code),
                    port_name=item.get("portname", item.get("port_name")),
                    country=item.get("country"),
                    transit_calls=item.get("n_total", item.get("transit_calls")),
                )
            )

        if not results:
            raise EmptyDataError("No port volume rows produced.")
        return results
