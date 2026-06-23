"""Sugra Commodity Spot Prices Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.commodity_spot_prices import (
    CommoditySpotPricesData,
    CommoditySpotPricesQueryParams,
)
from pydantic import Field


class SugraCommoditySpotPricesQueryParams(CommoditySpotPricesQueryParams):
    """Sugra Commodity Spot Prices Query Parameters."""

    commodity: str | None = Field(
        default=None,
        description="Filter to a single commodity id (e.g. gold, crude-oil-wti).",
    )


class SugraCommoditySpotPricesData(CommoditySpotPricesData):
    """Sugra Commodity Spot Prices Data."""

    title: str | None = Field(
        default=None, description="Descriptive title of the commodity series."
    )


def _normalize_date(raw: str) -> str:
    """Normalize a YYYY-MM or YYYY-MM-DD date string to YYYY-MM-DD."""
    raw = str(raw)
    parts = raw.split("-")
    if len(parts) == 2:
        return f"{raw}-01"
    return raw


class SugraCommoditySpotPricesFetcher(
    Fetcher[SugraCommoditySpotPricesQueryParams, list[SugraCommoditySpotPricesData]]
):
    """Fetch commodity spot prices from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCommoditySpotPricesQueryParams:
        """Transform the query parameters."""
        return SugraCommoditySpotPricesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCommoditySpotPricesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw commodity prices from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/commodities/prices", api_key)
        payload = envelope_data(response)
        prices = payload.get("prices", {}) if isinstance(payload, dict) else {}
        return prices or {}

    @staticmethod
    def transform_data(
        query: SugraCommoditySpotPricesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraCommoditySpotPricesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No commodity spot prices returned.")
        wanted = (query.commodity or "").strip().lower()
        rows: list[SugraCommoditySpotPricesData] = []
        for cid, entry in data.items():
            if not isinstance(entry, dict) or entry.get("value") is None:
                continue
            if wanted and wanted != cid.lower():
                continue
            rows.append(
                SugraCommoditySpotPricesData.model_validate(
                    {
                        "date": _normalize_date(entry.get("date")),
                        "symbol": cid,
                        "commodity": entry.get("title") or cid,
                        "price": entry.get("value"),
                        "unit": entry.get("units"),
                        "title": entry.get("title"),
                    }
                )
            )
        if not rows:
            raise EmptyDataError("No commodity spot prices matched the query.")
        return rows
