"""Sugra Forecast GDP Model (US, FOMC SEP via FRED)."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.gdp_forecast import (
    GdpForecastData,
    GdpForecastQueryParams,
)
from pydantic import Field

# Embedded VERBATIM from openbb_oecd.utils.constants (do NOT import openbb_oecd).
# Kept for param-shape parity with the OECD provider; only ``united_states`` is
# backed by a FRED series (GDPC1MD) on the Sugra proxy.
COUNTRY_TO_CODE_GDP_FORECAST = {
    "argentina": "ARG",
    "asia": "DAE",
    "australia": "AUS",
    "austria": "AUT",
    "belgium": "BEL",
    "brazil": "BRA",
    "bulgaria": "BGR",
    "canada": "CAN",
    "chile": "CHL",
    "china": "CHN",
    "colombia": "COL",
    "costa_rica": "CRI",
    "croatia": "HRV",
    "czech_republic": "CZE",
    "denmark": "DNK",
    "estonia": "EST",
    "finland": "FIN",
    "france": "FRA",
    "germany": "DEU",
    "greece": "GRC",
    "hungary": "HUN",
    "iceland": "ISL",
    "india": "IND",
    "indonesia": "IDN",
    "ireland": "IRL",
    "israel": "ISR",
    "italy": "ITA",
    "japan": "JPN",
    "korea": "KOR",
    "latvia": "LVA",
    "lithuania": "LTU",
    "luxembourg": "LUX",
    "mexico": "MEX",
    "netherlands": "NLD",
    "new_zealand": "NZL",
    "norway": "NOR",
    "peru": "PER",
    "poland": "POL",
    "portugal": "PRT",
    "romania": "ROU",
    "russia": "RUS",
    "slovak_republic": "SVK",
    "slovenia": "SVN",
    "south_africa": "ZAF",
    "spain": "ESP",
    "sweden": "SWE",
    "switzerland": "CHE",
    "turkey": "TUR",
    "united_kingdom": "GBR",
    "united_states": "USA",
    "other_major_oil_producers": "OIL_O",
    "rest_of_the_world": "WXD",
    "world": "W",
}

CODE_TO_COUNTRY_GDP_FORECAST = {
    v: k for k, v in COUNTRY_TO_CODE_GDP_FORECAST.items()
}

COUNTRIES = list(COUNTRY_TO_CODE_GDP_FORECAST) + ["all"]

# The single FRED series the Sugra proxy serves for this model: the FOMC
# Summary of Economic Projections median for real GDP growth (Q4/Q4 percent
# change, annual). This is the US-only forecast backing the model.
_SERIES_ID = "GDPC1MD"
_COUNTRY = "united_states"


class SugraGdpForecastQueryParams(GdpForecastQueryParams):
    """Sugra Forecast GDP Query Parameters.

    Mirrors the OECD GDP-forecast query shape (country / frequency / units) for
    parity, but only ``united_states`` is available: the data is the FOMC
    Summary of Economic Projections median real GDP growth (GDPC1MD), an annual
    percent forecast. ``frequency`` and ``units`` are accepted only at their
    backed values and reject anything else rather than silently downgrading.
    """

    __json_schema_extra__ = {
        "country": {
            "multiple_items_allowed": True,
            "choices": COUNTRIES,
        },
    }

    country: str = Field(
        description="Country to get forward GDP projections for. Only"
        " 'united_states' is available (FOMC SEP median real GDP growth).",
        default="united_states",
    )
    frequency: Literal["annual", "quarter"] = Field(
        default="annual",
        description="Frequency of the data; only 'annual' is available.",
    )
    units: Literal[
        "current_prices", "volume", "capita", "growth", "deflator"
    ] = Field(
        default="growth",
        description="Units of the data; only 'growth' (a percent) is available.",
        json_schema_extra={
            "choices": [
                "current_prices",
                "volume",
                "capita",
                "growth",
                "deflator",
            ]
        },
    )


class SugraGdpForecastData(GdpForecastData):
    """Sugra Forecast GDP Data."""


class SugraGdpForecastFetcher(
    Fetcher[SugraGdpForecastQueryParams, list[SugraGdpForecastData]]
):
    """Fetch the US GDP growth forecast (FOMC SEP, GDPC1MD) from the Sugra API.

    Source caveat: this is the Federal Reserve FOMC Summary of Economic
    Projections median for real GDP growth, NOT the OECD Economic Outlook. It is
    a faithful US GDP growth forecast from a different forecasting body.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraGdpForecastQueryParams:
        """Transform and validate the query (US / annual / growth only)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError

        transformed = params.copy()
        raw_country = transformed.get("country") or _COUNTRY
        countries = (
            raw_country.split(",")
            if isinstance(raw_country, str)
            else list(raw_country)
        )
        countries = [c.strip().lower() for c in countries if str(c).strip()]
        for country in countries:
            if country == "all":
                # 'all' means every OECD country; this US-only mirror cannot
                # honour it - return US rather than silently implying coverage.
                from warnings import warn

                warn("country='all' is unsupported here; returning united_states.")
                continue
            if country == _COUNTRY:
                continue
            if country in COUNTRY_TO_CODE_GDP_FORECAST:
                raise OpenBBError(
                    f"'{country}' is not available from this provider. Only"
                    " 'united_states' is supported (FOMC SEP forecast)."
                )
            raise OpenBBError(f"'{country}' is not a recognized country.")
        transformed["country"] = _COUNTRY

        frequency = transformed.get("frequency") or "annual"
        if frequency != "annual":
            raise OpenBBError(
                f"frequency '{frequency}' is not available; only 'annual' is."
            )
        units = transformed.get("units") or "growth"
        if units != "growth":
            raise OpenBBError(
                f"units '{units}' is not available; only 'growth' is."
            )
        return SugraGdpForecastQueryParams(**transformed)

    @staticmethod
    async def aextract_data(
        query: SugraGdpForecastQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw GDPC1MD series from the Sugra API."""
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
        query: SugraGdpForecastQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraGdpForecastData]:
        """Validate into the standard model.

        The FRED value is already a percent growth figure (e.g. 2.2). The
        standard ``GdpForecastData.value`` field carries no ``x-frontend_multiply``,
        so the value is stored AS-IS (no /100) - 2.2 stays 2.2.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows = fred_observations(data)
        if not rows:
            raise EmptyDataError("No GDP forecast observations returned.")
        return [
            SugraGdpForecastData.model_validate(
                {"date": r["date"], "country": _COUNTRY, "value": r["value"]}
            )
            for r in rows
        ]
