"""Sugra Country Interest Rates Model (OECD via FRED)."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.country_interest_rates import (
    CountryInterestRatesData,
    CountryInterestRatesQueryParams,
)
from pydantic import Field

# Verified country -> ISO2 map; every code below is live on FRED as an OECD
# main-economic-indicators mirror series (IR*01{ISO2}{FREQ}156N).
COUNTRY_TO_ISO2 = {
    "australia": "AU",
    "austria": "AT",
    "belgium": "BE",
    "canada": "CA",
    "chile": "CL",
    "czech_republic": "CZ",
    "denmark": "DK",
    "finland": "FI",
    "france": "FR",
    "germany": "DE",
    "greece": "GR",
    "hungary": "HU",
    "iceland": "IS",
    "ireland": "IE",
    "israel": "IL",
    "italy": "IT",
    "japan": "JP",
    "luxembourg": "LU",
    "mexico": "MX",
    "netherlands": "NL",
    "new_zealand": "NZ",
    "norway": "NO",
    "poland": "PL",
    "portugal": "PT",
    "russia": "RU",
    "slovakia": "SK",
    "slovenia": "SI",
    "south_africa": "ZA",
    "south_korea": "KR",
    "spain": "ES",
    "sweden": "SE",
    "switzerland": "CH",
    "united_kingdom": "GB",
    "united_states": "US",
}

# Duration -> FRED OECD series prefix. 'immediate' is the overnight/call-money
# rate, 'short' the 3-month interbank rate, 'long' the 10-year government bond.
DURATION_TO_PREFIX = {
    "long": "IRLTLT01",
    "short": "IR3TIB01",
    "immediate": "IRSTCI01",
}

# Frequency -> FRED series frequency code. M156N is monthly; the quarterly and
# annual mirrors are not published for every series, so they degrade to empty.
FREQUENCY_TO_CODE = {
    "monthly": "M",
    "quarter": "Q",
    "annual": "A",
}

COUNTRIES = list(COUNTRY_TO_ISO2)


class SugraCountryInterestRatesQueryParams(CountryInterestRatesQueryParams):
    """Sugra Country Interest Rates Query Parameters."""

    __json_schema_extra__ = {
        "country": {
            "multiple_items_allowed": True,
            "choices": COUNTRIES,
        },
        "frequency": {
            "multiple_items_allowed": False,
            "choices": list(FREQUENCY_TO_CODE),
        },
        "duration": {
            "multiple_items_allowed": False,
            "choices": list(DURATION_TO_PREFIX),
        },
    }

    duration: Literal["immediate", "short", "long"] = Field(
        default="long",
        description=(
            "Duration of the interest rate. 'immediate' is the overnight rate,"
            " 'short' is the 3-month rate, and 'long' is the 10-year rate."
        ),
    )
    frequency: Literal["monthly", "quarter", "annual"] = Field(
        default="monthly",
        description="Frequency to get interest rate for.",
    )


class SugraCountryInterestRatesData(CountryInterestRatesData):
    """Sugra Country Interest Rates Data."""


class SugraCountryInterestRatesFetcher(
    Fetcher[
        SugraCountryInterestRatesQueryParams,
        list[SugraCountryInterestRatesData],
    ]
):
    """Fetch OECD country interest rates (long/short/immediate) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCountryInterestRatesQueryParams:
        """Transform the query parameters."""
        return SugraCountryInterestRatesQueryParams(**params)

    @staticmethod
    def _series_to_country(
        query: SugraCountryInterestRatesQueryParams,
    ) -> dict[str, str]:
        """Resolve the requested countries to ``{FRED series id: country}``.

        An unsupported country raises an OpenBBError naming it; we never fall
        back to US data silently.
        """
        prefix = DURATION_TO_PREFIX[query.duration]
        freq = FREQUENCY_TO_CODE[query.frequency]
        requested = [
            c.strip().lower().replace(" ", "_")
            for c in (query.country or "united_states").split(",")
            if c.strip()
        ]
        mapping: dict[str, str] = {}
        for country in requested:
            iso2 = COUNTRY_TO_ISO2.get(country)
            if iso2 is None:
                raise OpenBBError(
                    f"Country '{country}' is not available for country_interest_rates."
                    f" Choose from: {', '.join(COUNTRIES)}."
                )
            mapping[f"{prefix}{iso2}{freq}156N"] = country
        return mapping

    @staticmethod
    async def aextract_data(
        query: SugraCountryInterestRatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw FRED series for each requested country from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        series_to_country = SugraCountryInterestRatesFetcher._series_to_country(query)
        payloads = await fred_series_payloads(
            api_key,
            list(series_to_country),
            start_date=query.start_date,
            end_date=query.end_date,
        )
        return {"series_to_country": series_to_country, "payloads": payloads}

    @staticmethod
    def transform_data(
        query: SugraCountryInterestRatesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraCountryInterestRatesData]:
        """Validate into the standard model (FRED percent -> fraction, value / 100)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        series_to_country = (data or {}).get("series_to_country") or {}
        payloads = (data or {}).get("payloads") or {}
        rows: list[SugraCountryInterestRatesData] = []
        for series_id, country in series_to_country.items():
            for obs in fred_observations(payloads.get(series_id, {})):
                rows.append(
                    SugraCountryInterestRatesData.model_validate(
                        {
                            "date": obs["date"],
                            # json_schema_extra x-frontend_multiply: 100 -> the
                            # stored value is a fraction, so divide the FRED percent.
                            "value": obs["value"] / 100,
                            "country": country,
                        }
                    )
                )
        if not rows:
            raise EmptyDataError("No country interest rate observations returned.")
        rows.sort(key=lambda r: (r.date, r.country or ""))
        return rows
