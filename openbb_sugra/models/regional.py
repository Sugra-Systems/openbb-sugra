"""Sugra FRED Regional (GeoFRED) Model.

`economy.fred_regional` is a FRED-provider-specific command - there is no
standard_models entry for it; the openbb-fred provider defines the model inline.
To add the `sugra` provider WITHOUT taking a hard dependency on openbb-fred, we
clean-room replicate its query/data shapes here, subclassing the openbb-core
SeriesQueryParams / SeriesData bases that openbb-fred itself builds on, and
register under the same `FredRegional` interface key.
"""

# pylint: disable=unused-argument

from datetime import date as dateType
from datetime import datetime
from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.fred_series import (
    SeriesData,
    SeriesQueryParams,
)
from pydantic import Field, model_validator


class SugraFredRegionalQueryParams(SeriesQueryParams):
    """Sugra FRED Regional Query Parameters (mirrors the fred provider)."""

    symbol: str = Field(
        description="The series_group ID (set is_series_group=True) or a series ID."
        " Not all FRED series carry geographical data."
    )
    is_series_group: bool = Field(
        default=False,
        description="When True, symbol is a series_group ID; else it is a series ID.",
    )
    region_type: (
        Literal["bea", "msa", "frb", "necta", "state", "country", "county", "censusregion"]
        | None
    ) = Field(
        default=None,
        description="The type of regional data. Required when is_series_group is True.",
    )
    season: Literal["sa", "nsa", "ssa"] = Field(
        default="nsa", description="The seasonal adjustment of the data."
    )
    units: str | None = Field(
        default=None,
        description="The units of the data. Required when is_series_group is True.",
    )
    frequency: (
        Literal[
            "a", "q", "m", "w", "d", "wef", "weth", "wew", "wetu", "wem",
            "wesu", "wesa", "bwew", "bwem",
        ]
        | None
    ) = Field(
        default=None,
        description="Frequency aggregation. Required when is_series_group is True.",
    )
    aggregation_method: Literal["avg", "sum", "eop"] | None = Field(
        default="eop", description="Aggregation method used for frequency aggregation."
    )
    transform: (
        Literal["chg", "ch1", "pch", "pc1", "pca", "cch", "cca", "log"] | None
    ) = Field(default=None, description="The value transformation.")

    @model_validator(mode="before")
    @classmethod
    def _require_group_fields(cls, values):
        """Group mode needs region_type/units/frequency; default its start_date."""
        if isinstance(values, dict) and values.get("is_series_group") is True:
            for key in ("frequency", "region_type", "units"):
                if values.get(key) is None:
                    raise ValueError(f"{key} is required when is_series_group is True.")
            if values.get("start_date") is None:
                values["start_date"] = "1900-01-01"
        return values


class SugraFredRegionalData(SeriesData):
    """Sugra FRED Regional Data."""

    region: str = Field(description="The name of the region.")
    code: str | int = Field(description="The code of the region.")
    value: int | float | None = Field(
        default=None, description="The observation value (units per the series)."
    )
    series_id: str = Field(description="The individual series ID for the region.")


class SugraFredRegionalFetcher(
    Fetcher[SugraFredRegionalQueryParams, list[SugraFredRegionalData]]
):
    """Fetch GeoFRED regional cross-sections from the Sugra API.

    Backed by `/api/v1/fred/regional`, which returns the whole region map in one
    call (no per-region fan-out). `value` is in the series' native units.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraFredRegionalQueryParams:
        """Transform the query parameters."""
        return SugraFredRegionalQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraFredRegionalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw regional payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {
            "symbol": query.symbol,
            "is_series_group": query.is_series_group,
            "season": query.season,
        }
        if query.is_series_group:
            params["region_type"] = query.region_type
            params["units"] = query.units
            params["frequency"] = query.frequency
            if query.aggregation_method:
                params["aggregation_method"] = query.aggregation_method
        if query.transform:
            params["transform"] = query.transform
        if query.start_date:
            params["start_date"] = str(query.start_date)
        response = await sugra_get("/api/v1/fred/regional", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraFredRegionalQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraFredRegionalData]:
        """Validate, end_date-filter, and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        results = (data or {}).get("results") or []
        if not results:
            raise EmptyDataError(
                f"No regional data returned for '{query.symbol}'."
            )
        rows: list[SugraFredRegionalData] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            row_date = item.get("date")
            if (
                query.end_date is not None
                and isinstance(row_date, str)
                and _parse_date(row_date) is not None
                and _parse_date(row_date) > query.end_date
            ):
                continue
            rows.append(SugraFredRegionalData.model_validate(item))
        if not rows:
            raise EmptyDataError(
                f"No regional observations for '{query.symbol}' matched the query."
            )
        return rows


def _parse_date(value: str) -> dateType | None:
    """Parse an ISO date string, or None when it is not YYYY-MM-DD."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
