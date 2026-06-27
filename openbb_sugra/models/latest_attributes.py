"""Sugra Latest Attributes Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.latest_attributes import (
    LatestAttributesData,
    LatestAttributesQueryParams,
)
from pydantic import Field, field_validator


class SugraLatestAttributesQueryParams(LatestAttributesQueryParams):
    """Sugra Latest Attributes Query Parameters.

    ``tag`` is a SEC XBRL concept name (e.g. ``Revenues``); both ``symbol`` and
    ``tag`` accept comma-separated lists and fan out over every combination.
    """

    __json_schema_extra__ = {
        "tag": {"multiple_items_allowed": True},
        "symbol": {"multiple_items_allowed": True},
    }

    @field_validator("tag", mode="before", check_fields=False)
    @classmethod
    def multiple_tags(cls, v: str | list[str] | set[str]):
        """Join tag lists but preserve case - XBRL concepts are case-sensitive."""
        if isinstance(v, str):
            return v
        return ",".join(list(v))


class SugraLatestAttributesData(LatestAttributesData):
    """Sugra Latest Attributes Data."""

    end: str | None = Field(
        default=None, description="Period-end date of the latest reported value."
    )
    unit: str | None = Field(
        default=None, description="Unit of measure for the value (e.g. USD)."
    )


class SugraLatestAttributesFetcher(
    Fetcher[SugraLatestAttributesQueryParams, list[SugraLatestAttributesData]]
):
    """Fetch the latest SEC XBRL concept value for each symbol/tag from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraLatestAttributesQueryParams:
        """Transform the query parameters."""
        return SugraLatestAttributesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraLatestAttributesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the latest concept row for each symbol/tag combination."""
        # pylint: disable=import-outside-toplevel
        import asyncio
        import logging

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        logger = logging.getLogger(__name__)
        api_key = get_api_key(credentials)
        symbols = [s.strip().upper() for s in query.symbol.split(",") if s.strip()]
        tags = [t.strip() for t in query.tag.split(",") if t.strip()]
        combos = [(sym, tag) for sym in symbols for tag in tags]

        async def fetch_one(symbol: str, tag: str) -> dict | None:
            response = await sugra_get(
                f"/api/v1/fundamentals/{symbol}/history/{tag}", api_key
            )
            payload = envelope_data(response)
            if not isinstance(payload, dict):
                return None
            rows = payload.get("data")
            if not isinstance(rows, list) or not rows:
                return None
            # The history rows are not strictly ordered; pick the most recent
            # period by end date and surface its as-reported value.
            latest = max(
                (r for r in rows if isinstance(r, dict) and r.get("end")),
                key=lambda r: r["end"],
                default=None,
            )
            if latest is None:
                return None
            return {
                "symbol": symbol,
                "tag": payload.get("concept") or tag,
                "value": latest.get("val"),
                "end": latest.get("end"),
                "unit": latest.get("unit"),
            }

        results = await asyncio.gather(
            *[fetch_one(sym, tag) for sym, tag in combos],
            return_exceptions=True,
        )
        rows: list[dict] = []
        for (sym, tag), result in zip(combos, results):
            if isinstance(result, BaseException):
                logger.warning(
                    "Sugra latest-attributes fetch failed for %s/%s: %s",
                    sym,
                    tag,
                    result,
                )
                continue
            if result is not None:
                rows.append(result)
        return rows

    @staticmethod
    def transform_data(
        query: SugraLatestAttributesQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraLatestAttributesData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No latest attribute values returned.")
        return [SugraLatestAttributesData.model_validate(d) for d in data]
