"""Sugra Share Price Index Model (OECD series via the Sugra FRED proxy)."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.share_price_index import (
    SharePriceIndexData,
    SharePriceIndexQueryParams,
)
from pydantic import field_validator

# Verified OECD country -> ISO 3166-1 alpha-2 map (40 countries). The FRED OECD
# share-price series are keyed by this alpha-2 code: SPASTT01{ISO2}{FREQ}661N.
_COUNTRY_TO_CODE = {
    "australia": "AU",
    "austria": "AT",
    "belgium": "BE",
    "brazil": "BR",
    "canada": "CA",
    "chile": "CL",
    "china": "CN",
    "czech_republic": "CZ",
    "denmark": "DK",
    "estonia": "EE",
    "finland": "FI",
    "france": "FR",
    "germany": "DE",
    "greece": "GR",
    "hungary": "HU",
    "iceland": "IS",
    "india": "IN",
    "indonesia": "ID",
    "ireland": "IE",
    "israel": "IL",
    "italy": "IT",
    "japan": "JP",
    "korea": "KR",
    "luxembourg": "LU",
    "mexico": "MX",
    "netherlands": "NL",
    "new_zealand": "NZ",
    "norway": "NO",
    "poland": "PL",
    "portugal": "PT",
    "russia": "RU",
    "slovak_republic": "SK",
    "slovenia": "SI",
    "south_africa": "ZA",
    "spain": "ES",
    "sweden": "SE",
    "switzerland": "CH",
    "turkey": "TR",
    "united_kingdom": "GB",
    "united_states": "US",
}

# Frequency -> FRED series-id letter. Monthly is the default; quarter/annual use
# the matching SPASTT01...{Q,A}661N variant and degrade to empty if unavailable.
_FREQUENCY_TO_LETTER = {"monthly": "M", "quarter": "Q", "annual": "A"}

_DEFAULT_COUNTRY = "united_states"


def _build_series_id(country: str, frequency: str) -> str:
    """Build the FRED OECD share-price series id for a country and frequency."""
    code = _COUNTRY_TO_CODE[country]
    letter = _FREQUENCY_TO_LETTER.get(frequency, "M")
    return f"SPASTT01{code}{letter}661N"


class SugraSharePriceIndexQueryParams(SharePriceIndexQueryParams):
    """Sugra Share Price Index Query Parameters.

    Mirrors the OECD provider: ``country`` accepts a comma-separated list and
    ``frequency`` selects monthly (default), quarter, or annual series.
    """

    __json_schema_extra__ = {
        "country": {
            "multiple_items_allowed": True,
            "choices": sorted(_COUNTRY_TO_CODE),
        }
    }

    @field_validator("country", mode="before", check_fields=False)
    @classmethod
    def validate_country(cls, c):
        """Validate country names against the supported OECD map.

        Unsupported countries raise a clear error instead of silently
        returning US data.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError

        if c is None:
            return _DEFAULT_COUNTRY
        values = [
            v.strip().lower().replace(" ", "_") for v in str(c).split(",") if v.strip()
        ]
        result: list[str] = []
        for v in values:
            if v in _COUNTRY_TO_CODE:
                result.append(v)
                continue
            raise OpenBBError(
                f"Unsupported country '{v}' for share_price_index. Supported "
                f"countries: {', '.join(sorted(_COUNTRY_TO_CODE))}."
            )
        if not result:
            return _DEFAULT_COUNTRY
        return ",".join(result)


class SugraSharePriceIndexData(SharePriceIndexData):
    """Sugra Share Price Index Data."""


class SugraSharePriceIndexFetcher(
    Fetcher[SugraSharePriceIndexQueryParams, list[SugraSharePriceIndexData]]
):
    """Fetch OECD share price indices (SPASTT01...661N) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraSharePriceIndexQueryParams:
        """Transform the query parameters."""
        return SugraSharePriceIndexQueryParams(**params)

    @staticmethod
    def _country_to_id(query: SugraSharePriceIndexQueryParams) -> dict[str, str]:
        """Map each requested country to its FRED share-price series id."""
        countries = (query.country or _DEFAULT_COUNTRY).split(",")
        return {c: _build_series_id(c, query.frequency) for c in countries}

    @staticmethod
    async def aextract_data(
        query: SugraSharePriceIndexQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw share-price series for each country from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        ids = list(SugraSharePriceIndexFetcher._country_to_id(query).values())
        return await fred_series_payloads(
            api_key,
            ids,
            start_date=query.start_date,
            end_date=query.end_date,
        )

    @staticmethod
    def transform_data(
        query: SugraSharePriceIndexQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraSharePriceIndexData]:
        """Validate into the standard model.

        The share price index is an as-is index (base 2015=100); the standard
        model declares no ``x-frontend_multiply``, so values pass through with
        no /100 rescale.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        country_to_id = SugraSharePriceIndexFetcher._country_to_id(query)
        rows: list[SugraSharePriceIndexData] = []
        for country, series_id in country_to_id.items():
            for obs in fred_observations((data or {}).get(series_id, {})):
                rows.append(
                    SugraSharePriceIndexData.model_validate(
                        {
                            "date": obs["date"],
                            "country": country,
                            "value": obs["value"],
                        }
                    )
                )
        if not rows:
            raise EmptyDataError("No share price index observations returned.")
        rows.sort(key=lambda r: (r.date, r.country or ""))
        return rows
