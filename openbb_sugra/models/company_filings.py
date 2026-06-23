"""Sugra Company Filings Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.company_filings import (
    CompanyFilingsData,
    CompanyFilingsQueryParams,
)
from pydantic import Field


class SugraCompanyFilingsQueryParams(CompanyFilingsQueryParams):
    """Sugra Company Filings Query Parameters."""

    form: str | None = Field(default=None, description="Filter by SEC form type (e.g. 10-K, 8-K).")
    date: str | None = Field(
        default=None,
        description="Daily-index date to browse (YYYY-MM-DD). Defaults to latest.",
    )
    cik: str | None = Field(default=None, description="Filter the daily index to a single CIK.")
    limit: int | None = Field(default=100, description="Maximum number of filings to return.")


class SugraCompanyFilingsData(CompanyFilingsData):
    """Sugra Company Filings Data."""

    cik: str | None = Field(default=None, description="The filer CIK.")
    company_name: str | None = Field(default=None, description="Name of the filing company.")
    accession: str | None = Field(default=None, description="SEC accession number of the filing.")


class SugraCompanyFilingsFetcher(
    Fetcher[SugraCompanyFilingsQueryParams, list[SugraCompanyFilingsData]]
):
    """Fetch SEC EDGAR daily-index filings from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCompanyFilingsQueryParams:
        """Transform the query parameters."""
        return SugraCompanyFilingsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCompanyFilingsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw daily-index filing metadata from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.form:
            params["form"] = query.form
        if query.date:
            params["date"] = query.date
        if query.cik:
            params["cik"] = query.cik
        if query.limit:
            params["limit"] = query.limit
        response = await sugra_get("/api/v1/sec/edgar/daily-index/by-form", api_key, params)
        payload = envelope_data(response)
        rows = payload.get("filings", []) if isinstance(payload, dict) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraCompanyFilingsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCompanyFilingsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No SEC filings returned.")

        results: list[SugraCompanyFilingsData] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            filed_at = item.get("filed_at")
            report_url = item.get("primary_doc_url") or item.get("filing_index_url")
            if not filed_at or not report_url:
                continue
            cik = item.get("cik")
            results.append(
                SugraCompanyFilingsData(
                    filing_date=filed_at,
                    report_type=item.get("form"),
                    report_url=report_url,
                    cik=None if cik is None else str(cik),
                    company_name=item.get("company_name"),
                    accession=item.get("accession"),
                )
            )

        if not results:
            raise EmptyDataError("No company filing rows produced.")
        return results
