"""Sugra Retail Prices model.

BLS average consumer prices (cost per unit) for an individual item, by US
region, served from the Sugra FRED proxy ``GET /api/v1/fred/series/{id}``. The
OpenBB ``openbb_fred`` provider is the reference for the item-keyword catalog
and the title-match resolution; it is not a dependency - the catalog is
mirrored verbatim in ``openbb_sugra.utils.retail_catalog`` and the matching is
reproduced here.

Item resolution mirrors the reference: the item name is matched as a substring
against the region's series titles, and every matching FRED series is fetched.
Values are dollar amounts (cost per unit) and are returned AS-IS - the standard
``RetailPricesData.value`` carries no ``x-frontend_multiply``.

The reference also exposes item-GROUP selectors ('meats', 'all_items', ...)
that expand to 20-80+ series per call. Those cold fan-outs overwhelm the
single-worker API (the profile that deferred the HQM curve), so this provider
ships individual items only and defers the group selectors to DATA-17.16.

The reference also exposes ``frequency`` and ``transform`` (FRED aggregation /
units). The Sugra proxy does not honour those FRED query parameters - it always
returns the native monthly levels - so this provider deliberately omits them
rather than advertise options it cannot serve. They are a clean follow-up if
the endpoint gains ``frequency`` / ``units`` passthrough.
"""

from __future__ import annotations

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.retail_prices import (
    RetailPricesData,
    RetailPricesQueryParams,
)
from pydantic import Field, field_validator

from openbb_sugra.utils.retail_catalog import ALL_ITEMS, ITEM_GROUPS, REGION_SYMBOLS

_REGIONS = ["all_city", "northeast", "midwest", "south", "west"]
_GROUP_KEYS = set(ITEM_GROUPS)
_DEFAULT_ITEM = "gasoline"


def _matches(item: str) -> bool:
    """Whether an item keyword hits at least one series title in any region."""
    needle = item.replace("_", " ")
    return any(
        needle in title.lower()
        for symbols in REGION_SYMBOLS.values()
        for title in symbols.values()
    )


# Only individual items ship here. The group / all_items selectors fan out to
# 20-80+ cold FRED fetches per call and overwhelm the single-worker API (the
# same profile that deferred the HQM curve), so they are deferred to DATA-17.16
# pending a bulk endpoint. Drop the group names and the never-matching
# reference typos so the advertised choices are exactly what resolves.
_ITEM_CHOICES = sorted(i for i in ALL_ITEMS if i not in _GROUP_KEYS and _matches(i))


class SugraRetailPricesQueryParams(RetailPricesQueryParams):
    """Sugra Retail Prices Query Parameters."""

    __json_schema_extra__ = {
        "item": {"multiple_items_allowed": False, "choices": _ITEM_CHOICES},
        "country": {"multiple_items_allowed": False, "choices": ["united_states"]},
        "region": {"multiple_items_allowed": False, "choices": _REGIONS},
    }

    item: str | None = Field(
        default=_DEFAULT_ITEM,
        description="The individual item to get average prices for (e.g."
        " 'gasoline', 'milk', 'electricity'). Item-group selectors ('meats',"
        " 'all_items', ...) are deferred to a future release.",
    )
    country: Literal["united_states"] = Field(
        default="united_states",
        description="The country - only the United States is available.",
    )
    region: Literal["all_city", "northeast", "midwest", "south", "west"] = Field(
        default="all_city",
        description="The US region to get average price levels for.",
    )

    @field_validator("item", mode="before", check_fields=False)
    @classmethod
    def _default_item(cls, v):
        """Default a missing item to a single representative item."""
        return _DEFAULT_ITEM if v is None else v


class SugraRetailPricesData(RetailPricesData):
    """Sugra Retail Prices Data."""


class SugraRetailPricesFetcher(
    Fetcher[SugraRetailPricesQueryParams, list[SugraRetailPricesData]]
):
    """Fetch BLS average retail prices from the Sugra FRED proxy."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraRetailPricesQueryParams:
        """Transform the query."""
        return SugraRetailPricesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraRetailPricesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Resolve the item to FRED series and fetch them from the proxy."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError

        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        # Normalise once so case/underscore variants match (and a mis-cased
        # group name still gets the deferral message, not a blank no-match).
        item = (query.item or _DEFAULT_ITEM).lower()
        if item in _GROUP_KEYS:
            raise OpenBBError(
                f"Item group '{item}' is deferred (board item DATA-17.16): it"
                " fans out to many cold series per call. Request an individual"
                " item instead, e.g. 'gasoline', 'milk', 'electricity'."
            )
        # Match the item keyword as a substring of the series title, exactly as
        # the openbb_fred reference does (underscores become spaces).
        symbols = REGION_SYMBOLS[query.region]
        needle = item.replace("_", " ")
        series_ids = [
            sid for sid, title in symbols.items() if needle in title.lower()
        ]
        if not series_ids:
            known = item in _ITEM_CHOICES
            detail = (
                f"'{item}' has no series in region '{query.region}' - try"
                " another region."
                if known
                else f"'{item}' is not a known item. Choose from:"
                f" {', '.join(_ITEM_CHOICES)}."
            )
            raise OpenBBError(detail)

        api_key = get_api_key(credentials)
        payloads = await fred_series_payloads(
            api_key,
            series_ids,
            start_date=query.start_date,
            end_date=query.end_date,
        )
        return {"region": query.region, "payloads": payloads}

    @staticmethod
    def transform_data(
        query: SugraRetailPricesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraRetailPricesData]:
        """Melt the per-series payloads into standard rows (values AS-IS)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        symbols = REGION_SYMBOLS[data["region"]]
        rows: list[dict] = []
        for series_id, payload in data["payloads"].items():
            description = symbols.get(series_id, series_id).strip()
            for obs in fred_observations(payload):
                rows.append(
                    {
                        "date": obs["date"],
                        "symbol": series_id,
                        "description": description,
                        "value": obs["value"],
                        "country": "united_states",
                    }
                )

        if not rows:
            raise EmptyDataError("No retail price observations returned.")
        rows.sort(key=lambda r: (str(r["date"]), r["description"]))
        return [SugraRetailPricesData.model_validate(r) for r in rows]
