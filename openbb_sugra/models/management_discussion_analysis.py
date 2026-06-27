"""Sugra Management Discussion & Analysis Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.management_discussion_analysis import (
    ManagementDiscussionAnalysisData,
    ManagementDiscussionAnalysisQueryParams,
)
from pydantic import Field


class SugraManagementDiscussionAnalysisQueryParams(
    ManagementDiscussionAnalysisQueryParams
):
    """Sugra Management Discussion & Analysis Query.

    The Sugra SEC EDGAR endpoint serves the MD&A (Item 7) of the most recent
    10-K filing for the symbol; ``calendar_year`` / ``calendar_period`` are
    accepted for interface parity but the endpoint always returns the latest
    annual report.
    """


class SugraManagementDiscussionAnalysisData(ManagementDiscussionAnalysisData):
    """Sugra Management Discussion & Analysis Data."""

    url: str | None = Field(
        default=None,
        description="The URL of the filing from which the MD&A was extracted.",
    )


def _eight_digit_date(text: str) -> str | None:
    """Pull a YYYYMMDD date from text (e.g. an SEC primary-document filename).

    SEC primary documents are commonly named ``<ticker>-YYYYMMDD.htm`` where
    the date is the fiscal-period end. Returns an ISO ``YYYY-MM-DD`` string, or
    ``None`` when no plausible 8-digit date is present.
    """
    # pylint: disable=import-outside-toplevel
    import re

    for match in re.findall(r"(\d{8})", text or ""):
        year, month, day = match[:4], match[4:6], match[6:8]
        if "1994" <= year <= "2099" and "01" <= month <= "12" and "01" <= day <= "31":
            return f"{year}-{month}-{day}"
    return None


class SugraManagementDiscussionAnalysisFetcher(
    Fetcher[
        SugraManagementDiscussionAnalysisQueryParams,
        SugraManagementDiscussionAnalysisData,
    ]
):
    """Management Discussion & Analysis (10-K Item 7) via the Sugra API.

    Sugra parses the MD&A free-text out of the company's most recent 10-K
    filing server-side, so this fetcher makes one (or, for very long sections,
    a few chunked) Sugra call(s) and concatenates the result - no client-side
    HTML-to-markdown extraction needed.
    """

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraManagementDiscussionAnalysisQueryParams:
        """Transform the query parameters."""
        return SugraManagementDiscussionAnalysisQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraManagementDiscussionAnalysisQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the MD&A record (all chunks concatenated) from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        path = f"/api/v1/sec/edgar/{query.symbol}/10-k/items/7"

        response = await sugra_get(path, api_key)
        record = envelope_data(response)
        if not isinstance(record, dict) or not record:
            raise EmptyDataError(
                f"No 10-K MD&A (Item 7) found for the symbol -> {query.symbol}"
            )

        parts = [record.get("content") or ""]

        # The endpoint caps content per response; when the section spans
        # multiple chunks, pull the remaining chunks and concatenate in order.
        chunk_count = record.get("chunk_count") or 1
        try:
            chunk_count = int(chunk_count)
        except (TypeError, ValueError):
            chunk_count = 1

        for chunk in range(1, chunk_count):
            extra = envelope_data(await sugra_get(path, api_key, {"chunk": chunk}))
            if isinstance(extra, dict) and extra.get("content"):
                parts.append(extra["content"])

        record["content"] = "".join(parts).strip()
        if not record["content"]:
            raise EmptyDataError(
                f"The 10-K MD&A (Item 7) is empty for the symbol -> {query.symbol}"
            )
        return record

    @staticmethod
    def transform_data(
        query: SugraManagementDiscussionAnalysisQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> SugraManagementDiscussionAnalysisData:
        """Map the Sugra MD&A record onto the standard model.

        ``calendar_year`` / ``calendar_period`` are derived from the fiscal
        period-end (parsed from the primary-document filename) when available,
        otherwise from the filing date. No percent normalisation applies - the
        payload is free-text MD&A.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError
        from pandas import to_datetime

        content = data.get("content") or ""
        if not content:
            raise EmptyDataError("No MD&A content returned.")

        url = data.get("primary_document_url")
        period_ending = _eight_digit_date(url or "")
        # Fall back to the filing date when the filename carries no period end.
        anchor = period_ending or data.get("filing_date")
        if not anchor:
            raise EmptyDataError(
                "The MD&A record carries no filing or period date to derive the"
                f" calendar year/period for the symbol -> {query.symbol}"
            )
        stamp = to_datetime(anchor)

        return SugraManagementDiscussionAnalysisData(
            symbol=query.symbol,
            calendar_year=int(stamp.year),
            calendar_period=int(stamp.quarter),
            period_ending=period_ending,
            content=content,
            url=url,
        )
