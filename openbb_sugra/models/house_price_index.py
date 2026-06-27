"""Sugra House Price Index Model (US, from FRED USSTHPI)."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.house_price_index import (
    HousePriceIndexData,
    HousePriceIndexQueryParams,
)
from pydantic import field_validator

# Country -> OECD code map, embedded verbatim from openbb_oecd
# (utils.constants.COUNTRY_TO_CODE_RGDP) so this provider stays
# import-independent of openbb_oecd. Only the US is backed by a FRED series;
# the rest are kept solely to validate/normalise the country name.
COUNTRY_TO_CODE_RGDP = {
    "G20": "G-20",
    "G7": "G-7",
    "argentina": "ARG",
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
    "euro_area_20": "EA20",
    "euro_area_19": "EA19",
    "europe": "OECDE",
    "european_union_27": "EU27_2020",
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
    "oecd_total": "OECD",
    "poland": "POL",
    "portugal": "PRT",
    "romania": "ROU",
    "russia": "RUS",
    "saudi_arabia": "SAU",
    "slovak_republic": "SVK",
    "slovenia": "SVN",
    "south_africa": "ZAF",
    "spain": "ESP",
    "sweden": "SWE",
    "switzerland": "CHE",
    "turkey": "TUR",
    "united_kingdom": "GBR",
    "united_states": "USA",
}
CODE_TO_COUNTRY_RGDP = {v: k for k, v in COUNTRY_TO_CODE_RGDP.items()}

# The only country with a backing FRED series. USSTHPI = "All-Transactions
# House Price Index for the United States", Index 1980:Q1=100, quarterly.
_SUPPORTED_COUNTRY = "united_states"
_US_SERIES_ID = "USSTHPI"


class SugraHousePriceIndexQueryParams(HousePriceIndexQueryParams):
    """Sugra House Price Index Query Parameters.

    US-only: served from FRED USSTHPI. The standard ``frequency`` and
    ``transform`` params are honoured (the source is quarterly; ``transform``
    is computed from the single index series).
    """

    @field_validator("country", mode="before", check_fields=False)
    @classmethod
    def validate_country(cls, c):
        """Normalise and reject any non-US country (US-only source)."""
        if c is None:
            return _SUPPORTED_COUNTRY
        value = str(c).strip().replace(" ", "_")
        # Accept an OECD code (e.g. "USA") or a country name (e.g. "united_states").
        if value.upper() in CODE_TO_COUNTRY_RGDP:
            value = CODE_TO_COUNTRY_RGDP[value.upper()]
        else:
            value = value.lower()
        if value != _SUPPORTED_COUNTRY:
            raise OpenBBError(
                f"Unsupported country '{c}'. The Sugra house price index is "
                "US-only (FRED USSTHPI); use country='united_states'."
            )
        return value


class SugraHousePriceIndexData(HousePriceIndexData):
    """Sugra House Price Index Data."""


class SugraHousePriceIndexFetcher(
    Fetcher[SugraHousePriceIndexQueryParams, list[SugraHousePriceIndexData]]
):
    """Fetch the US All-Transactions House Price Index (FRED USSTHPI) via Sugra."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraHousePriceIndexQueryParams:
        """Transform the query parameters."""
        return SugraHousePriceIndexQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraHousePriceIndexQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw USSTHPI index series from the Sugra FRED proxy."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {"limit": 1000, "sort_order": "desc"}
        # yoy/period need the lookback quarters BEFORE start_date to compute the
        # change AT start_date, so only window the index transform here; the
        # change transforms fetch full history and trim in transform_data.
        if query.start_date and (query.transform or "index") == "index":
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        response = await sugra_get(
            f"/api/v1/fred/series/{_US_SERIES_ID}", api_key, params
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraHousePriceIndexQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraHousePriceIndexData]:
        """Validate into the standard model.

        ``transform='index'`` returns the raw USSTHPI value AS-IS (the standard
        ``value`` field carries no ``x-frontend_multiply``, so no /100). ``yoy``
        and ``period`` are percent changes computed from that index: ``yoy`` vs
        the same quarter one year earlier, ``period`` vs the previous quarter
        (mirroring OECD PA/PC, but derived from the single FRED series).
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows = fred_observations(data)
        if not rows:
            raise EmptyDataError("No house price index observations returned.")

        transform = query.transform or "index"
        by_date = {r["date"]: r["value"] for r in rows}
        results: list[SugraHousePriceIndexData] = []
        for idx, row in enumerate(rows):
            date = row["date"]
            value = row["value"]
            if transform == "index":
                out = value
            elif transform == "period":
                if idx == 0:
                    continue
                prev = rows[idx - 1]["value"]
                if not prev:
                    continue
                out = (value / prev - 1.0) * 100.0
            else:  # yoy: same period one year earlier
                prior_year = f"{int(date[:4]) - 1}{date[4:]}"
                prev = by_date.get(prior_year)
                if not prev:
                    continue
                out = (value / prev - 1.0) * 100.0
            results.append(
                SugraHousePriceIndexData.model_validate(
                    {"date": date, "country": _SUPPORTED_COUNTRY, "value": out}
                )
            )

        # yoy/period fetched full history for the lookback; trim back to the
        # requested window now that the changes at start_date are computed.
        if query.start_date and transform in ("yoy", "period"):
            start = str(query.start_date)
            results = [r for r in results if str(r.date) >= start]

        if not results:
            raise EmptyDataError("No house price index observations returned.")
        return results
