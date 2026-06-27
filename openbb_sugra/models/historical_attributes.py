"""Sugra Historical Attributes Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.historical_attributes import (
    HistoricalAttributesData,
    HistoricalAttributesQueryParams,
)
from pydantic import field_validator


class SugraHistoricalAttributesQueryParams(HistoricalAttributesQueryParams):
    """Sugra Historical Attributes Query Parameters.

    Both ``symbol`` and ``tag`` accept comma-separated lists; the fetcher loops
    every (symbol, tag) pair. ``tag`` is a us-gaap (or other XBRL taxonomy)
    concept name, which IS case-sensitive on the backing SEC endpoint (``Assets``
    resolves, ``assets`` 404s), so - unlike the standard Intrinio model - the
    casing is preserved here rather than lower-cased.
    """

    __json_schema_extra__ = {
        "symbol": {"multiple_items_allowed": True},
        "tag": {"multiple_items_allowed": True},
    }

    @field_validator("tag", mode="before", check_fields=False)
    @classmethod
    def multiple_tags(cls, v: str | list[str] | set[str]) -> str:
        """Join a list/set of tags into a comma string, preserving case.

        Overrides the standard model's validator, which lower-cases - the Sugra
        SEC concept endpoint matches concept names case-sensitively.
        """
        if isinstance(v, str):
            return v
        return ",".join(str(tag) for tag in list(v))


class SugraHistoricalAttributesData(HistoricalAttributesData):
    """Sugra Historical Attributes Data."""


class SugraHistoricalAttributesFetcher(
    Fetcher[
        SugraHistoricalAttributesQueryParams,
        list[SugraHistoricalAttributesData],
    ]
):
    """Historical values of an XBRL concept (us-gaap tag) for an equity via the Sugra API.

    Backed by the SEC company-facts history endpoint
    (``/api/v1/fundamentals/{ticker}/history/{concept}``). The reported ``value``
    is the RAW XBRL fact value, carried through as-is - no normalisation.
    """

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraHistoricalAttributesQueryParams:
        """Transform the query parameters."""
        return SugraHistoricalAttributesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraHistoricalAttributesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return one mapped row per concept fact across all (symbol, tag) pairs."""
        # pylint: disable=import-outside-toplevel
        import asyncio

        from openbb_sugra.utils.helpers import (
            envelope_data,
            get_api_key,
            sugra_get,
        )

        api_key = get_api_key(credentials)
        symbols = [s.strip().upper() for s in (query.symbol or "").split(",") if s.strip()]
        tags = [t.strip() for t in (query.tag or "").split(",") if t.strip()]
        start = str(query.start_date) if query.start_date else None
        end = str(query.end_date) if query.end_date else None

        semaphore = asyncio.Semaphore(8)

        async def _one(symbol: str, tag: str) -> list[dict]:
            async with semaphore:
                response = await sugra_get(
                    f"/api/v1/fundamentals/{symbol}/history/{tag}",
                    api_key,
                )
            payload = envelope_data(response)
            if not isinstance(payload, dict):
                return []
            concept = payload.get("concept") or tag
            facts = payload.get("data") or []
            rows: list[dict] = []
            for fact in facts:
                if not isinstance(fact, dict):
                    continue
                fact_end = fact.get("end")
                if not fact_end:
                    continue
                if start and fact_end < start:
                    continue
                if end and fact_end > end:
                    continue
                rows.append(
                    {
                        "date": fact_end,
                        "symbol": symbol,
                        "tag": concept,
                        "value": fact.get("val"),
                    }
                )
            return rows

        pairs = [(s, t) for s in symbols for t in tags]
        results = await asyncio.gather(*[_one(s, t) for s, t in pairs])
        return [row for batch in results for row in batch]

    @staticmethod
    def transform_data(
        query: SugraHistoricalAttributesQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraHistoricalAttributesData]:
        """Sort, limit, and validate into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No historical attribute values returned.")
        reverse = (query.sort or "desc").lower() == "desc"
        rows = sorted(data, key=lambda r: (r["date"], r["symbol"], r["tag"]), reverse=reverse)
        if query.limit:
            rows = rows[: query.limit]
        return [SugraHistoricalAttributesData.model_validate(r) for r in rows]
