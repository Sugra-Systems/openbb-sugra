"""Sugra Composite Leading Indicator Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.composite_leading_indicator import (
    CompositeLeadingIndicatorData,
    CompositeLeadingIndicatorQueryParams,
)
from pydantic import Field

# OECD country -> code map (mirrored verbatim from the openbb_oecd reference
# model). The OECD CLI exposes every country below over SDMX, but FRED has
# discontinued the OECD CLI series for non-US countries (DEU/JPN now 502); only
# the US amplitude-adjusted series remains live, so this provider serves the US
# alone. The map is kept whole so the supported-country gate is explicit.
COUNTRIES = {
    "g20": "G20",
    "g7": "G7",
    "asia5": "A5M",
    "north_america": "NAFTA",
    "europe4": "G4E",
    "australia": "AUS",
    "brazil": "BRA",
    "canada": "CAN",
    "china": "CHN",
    "france": "FRA",
    "germany": "DEU",
    "india": "IND",
    "indonesia": "IDN",
    "italy": "ITA",
    "japan": "JPN",
    "mexico": "MEX",
    "spain": "ESP",
    "south_africa": "ZAF",
    "south_korea": "KOR",
    "turkey": "TUR",
    "united_states": "USA",
    "united_kingdom": "GBR",
}

# The only FRED OECD CLI series still published: US, amplitude-adjusted, long
# term average = 100. The standard model marks ``value`` as an index unit with
# no ``x-frontend_multiply``, so the value is taken AS-IS (no /100).
_SERIES_ID = "USALOLITONOSTSAM"
_DEFAULT_COUNTRY = "united_states"


class SugraCompositeLeadingIndicatorQueryParams(CompositeLeadingIndicatorQueryParams):
    """Sugra Composite Leading Indicator Query Parameters."""

    country: str = Field(
        default=_DEFAULT_COUNTRY,
        description="Country to get the CLI for. Only 'united_states' is"
        + " available via this provider (FRED discontinued the non-US series).",
    )


class SugraCompositeLeadingIndicatorData(CompositeLeadingIndicatorData):
    """Sugra Composite Leading Indicator Data."""


class SugraCompositeLeadingIndicatorFetcher(
    Fetcher[
        SugraCompositeLeadingIndicatorQueryParams,
        list[SugraCompositeLeadingIndicatorData],
    ]
):
    """Fetch the OECD Composite Leading Indicator (US, USALOLITONOSTSAM)."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCompositeLeadingIndicatorQueryParams:
        """Transform the query; reject unsupported (non-US) countries."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError

        raw = params.get("country") or _DEFAULT_COUNTRY
        requested = raw if isinstance(raw, list) else str(raw).split(",")
        requested = [c.strip().lower() for c in requested if str(c).strip()]
        if any(c not in (_DEFAULT_COUNTRY, "usa") for c in requested):
            raise OpenBBError(
                "only united_states available via this provider"
                + f" (requested '{raw}')."
            )
        params = {**params, "country": _DEFAULT_COUNTRY}
        return SugraCompositeLeadingIndicatorQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCompositeLeadingIndicatorQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw US CLI series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {"limit": 1000, "sort_order": "desc"}
        if query.start_date:
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        response = await sugra_get(f"/api/v1/fred/series/{_SERIES_ID}", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraCompositeLeadingIndicatorQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraCompositeLeadingIndicatorData]:
        """Validate into the standard model (the CLI index value is as-is)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows = fred_observations(data)
        if not rows:
            raise EmptyDataError("No Composite Leading Indicator observations returned.")
        return [
            SugraCompositeLeadingIndicatorData.model_validate(
                {"date": r["date"], "value": r["value"], "country": _DEFAULT_COUNTRY}
            )
            for r in rows
        ]
