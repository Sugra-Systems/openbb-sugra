"""Sugra Compare Company Facts Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.compare_company_facts import (
    CompareCompanyFactsData,
    CompareCompanyFactsQueryParams,
)
from pydantic import Field


class SugraCompareCompanyFactsQueryParams(CompareCompanyFactsQueryParams):
    """Sugra Compare Company Facts Query Parameters."""

    fact: str = Field(
        default="Revenues",
        description="XBRL concept to rank companies by (e.g. Revenues, Assets, NetIncomeLoss).",
    )
    period: str | None = Field(
        default=None,
        description="Reporting frame (e.g. CY2024, CY2024Q1, CY2024Q4I). Defaults to latest.",
    )
    unit: str | None = Field(
        default=None,
        description="XBRL unit of measure (USD, USD/shares, shares, pure). Defaults to USD.",
    )
    taxonomy: str | None = Field(
        default=None,
        description="XBRL taxonomy to query (us-gaap or dei). Defaults to us-gaap.",
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of companies to return (top N by value).",
    )
    sort: str | None = Field(
        default=None,
        description="Sort direction by reported value (asc or desc). Defaults to desc.",
    )


class SugraCompareCompanyFactsData(CompareCompanyFactsData):
    """Sugra Compare Company Facts Data."""

    cik: str | None = Field(default=None, description="Central Index Key of the entity.")
    unit: str | None = Field(default=None, description="XBRL unit of measure for the value.")
    rank: int | None = Field(default=None, description="Rank of the entity within the frame.")


class SugraCompareCompanyFactsFetcher(
    Fetcher[SugraCompareCompanyFactsQueryParams, list[SugraCompareCompanyFactsData]]
):
    """Rank companies by a single XBRL concept (SEC frames) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCompareCompanyFactsQueryParams:
        """Transform the query parameters."""
        return SugraCompareCompanyFactsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCompareCompanyFactsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw cross-company XBRL frame from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        concept = (query.fact or "").strip()
        if not concept:
            raise EmptyDataError("A `fact` (XBRL concept) is required for the frames lookup.")

        params: dict[str, Any] = {}
        if query.period:
            params["period"] = query.period
        if query.unit:
            params["unit"] = query.unit
        if query.taxonomy:
            params["taxonomy"] = query.taxonomy
        if query.limit:
            params["top_n"] = query.limit
        if query.sort:
            params["sort"] = query.sort

        response = await sugra_get(
            f"/api/v1/fundamentals/frames/{concept}", api_key, params
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraCompareCompanyFactsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraCompareCompanyFactsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError
        from pydantic import ValidationError

        ranking = data.get("ranking") if isinstance(data, dict) else None
        if not ranking:
            raise EmptyDataError("No company ranking returned for the requested concept.")

        unit = data.get("unit")
        results: list[SugraCompareCompanyFactsData] = []
        for item in ranking:
            if not isinstance(item, dict):
                continue
            val = item.get("val")
            if val is None:
                continue
            end = item.get("end")
            fiscal_year: int | None = None
            if isinstance(end, str) and len(end) >= 4 and end[:4].isdigit():
                fiscal_year = int(end[:4])
            cik = item.get("cik")
            # Skip a single malformed row rather than sink the whole ranking.
            try:
                results.append(
                    SugraCompareCompanyFactsData(
                        name=item.get("entity_name"),
                        value=val,
                        period_ending=end,
                        period_beginning=item.get("start"),
                        fiscal_year=fiscal_year,
                        cik=None if cik is None else str(cik),
                        unit=unit,
                        rank=item.get("rank"),
                    )
                )
            except ValidationError:
                continue

        if not results:
            raise EmptyDataError("No company fact rows produced.")
        return results
