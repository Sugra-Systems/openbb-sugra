"""Sugra Latest Financial Reports Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.latest_financial_reports import (
    LatestFinancialReportsData,
    LatestFinancialReportsQueryParams,
)
from pydantic import Field


class SugraLatestFinancialReportsQueryParams(LatestFinancialReportsQueryParams):
    """Sugra Latest Financial Reports Query Parameters."""

    form: str | None = Field(
        default="10-K,10-Q",
        description="Comma-separated SEC form types to browse (e.g. 10-K,10-Q).",
    )
    cik: str | None = Field(default=None, description="Filter the daily index to a single CIK.")
    limit: int | None = Field(default=50, description="Maximum number of filings per form type.")


class SugraLatestFinancialReportsData(LatestFinancialReportsData):
    """Sugra Latest Financial Reports Data."""

    accession: str | None = Field(default=None, description="SEC accession number of the filing.")
    primary_doc_url: str | None = Field(
        default=None, description="URL to the primary filing document."
    )


class SugraLatestFinancialReportsFetcher(
    Fetcher[
        SugraLatestFinancialReportsQueryParams,
        list[SugraLatestFinancialReportsData],
    ]
):
    """Fetch the latest periodic financial reports from the Sugra SEC EDGAR daily index.

    Defaults to the most recent 10-K (annual) and 10-Q (quarterly) filings. Each
    requested form type is a separate daily-index call; the rows are merged and
    presented newest filing first.
    """

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraLatestFinancialReportsQueryParams:
        """Transform the query parameters."""
        return SugraLatestFinancialReportsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraLatestFinancialReportsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw daily-index filing metadata for each requested form type."""
        # pylint: disable=import-outside-toplevel
        import asyncio

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        forms = [f.strip() for f in (query.form or "10-K,10-Q").split(",") if f.strip()]

        async def _one(form: str) -> list[dict]:
            params: dict[str, Any] = {"form": form}
            if query.cik:
                params["cik"] = query.cik
            if query.limit:
                params["limit"] = query.limit
            response = await sugra_get(
                "/api/v1/sec/edgar/daily-index/by-form", api_key, params
            )
            payload = envelope_data(response)
            return payload.get("filings", []) if isinstance(payload, dict) else []

        results = await asyncio.gather(*[_one(form) for form in forms])
        rows: list[dict] = []
        for batch in results:
            rows.extend(batch)
        return rows

    @staticmethod
    def transform_data(
        query: SugraLatestFinancialReportsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraLatestFinancialReportsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError
        from pydantic import ValidationError

        if not data:
            raise EmptyDataError("No SEC financial reports returned.")

        results: list[SugraLatestFinancialReportsData] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            filed_at = item.get("filed_at")
            url = item.get("filing_index_url") or item.get("primary_doc_url")
            if not filed_at or not url:
                continue
            cik = item.get("cik")
            # Skip a single malformed row (e.g. an unparseable filed date)
            # rather than sink the whole result set.
            try:
                results.append(
                    SugraLatestFinancialReportsData(
                        filing_date=str(filed_at)[:10],
                        url=url,
                        name=item.get("company_name"),
                        cik=None if cik is None else str(cik),
                        report_type=item.get("form"),
                        accession=item.get("accession"),
                        primary_doc_url=item.get("primary_doc_url"),
                    )
                )
            except ValidationError:
                continue

        if not results:
            raise EmptyDataError("No financial report rows produced.")
        results.sort(key=lambda r: r.filing_date, reverse=True)
        return results
