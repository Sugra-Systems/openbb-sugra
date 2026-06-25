"""Sugra Congress Bills Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_congress_gov.models.congress_bills import (
    CongressBillsData,
    CongressBillsQueryParams,
)
from openbb_core.provider.abstract.fetcher import Fetcher


def _within_update_window(
    rows: list, start: dateType | None, end: dateType | None
) -> list:
    """Keep rows whose ``update_date`` falls in [start, end].

    The Sugra congress endpoint does not filter by date server-side, so the
    standard model's start_date/end_date ("filter by last updated date") are
    applied here. Bounds are open-ended when None; a row without an update_date
    is kept (it cannot be evaluated). Filtering is bounded to the fetched page.
    """
    if start is None and end is None:
        return rows
    kept = []
    for row in rows:
        updated = getattr(row, "update_date", None)
        if updated is not None:
            if start is not None and updated < start:
                continue
            if end is not None and updated > end:
                continue
        kept.append(row)
    return kept


class SugraCongressBillsFetcher(Fetcher[CongressBillsQueryParams, list[CongressBillsData]]):
    """List current and historical U.S. Congressional bills from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> CongressBillsQueryParams:
        """Transform the query parameters."""
        return CongressBillsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: CongressBillsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw bill list from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        # The Sugra endpoint cannot honour these, so reject them rather than
        # silently returning page 1 / a misleading empty result.
        if query.offset:
            raise OpenBBError(
                "The Sugra congress provider does not support offset pagination."
            )
        if query.limit == 0:
            raise OpenBBError(
                "The Sugra congress provider does not support unbounded fetch "
                "(limit=0); pass a positive limit (max 250)."
            )

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.congress is not None:
            params["congress"] = query.congress
        if query.bill_type is not None:
            params["bill_type"] = query.bill_type
        if query.limit is not None:
            params["limit"] = query.limit
        response = await sugra_get("/api/v1/congress/bills", api_key, params)
        payload = envelope_data(response)
        return payload.get("bills", []) if isinstance(payload, dict) else []

    @staticmethod
    def transform_data(
        query: CongressBillsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[CongressBillsData]:
        """Validate, transform, and apply the client-side date window.

        Sugra serves the congress.gov bill shape verbatim, so the canonical
        congress.gov transform maps it faithfully. start_date/end_date are
        applied client-side (the Sugra endpoint ignores them), bounded to the
        fetched page.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_congress_gov.models.congress_bills import CongressBillsFetcher
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No Congressional bills returned.")
        # Sugra emits `latestAction: null` for placeholder bills (e.g. "Reserved
        # for the Speaker"); the congress.gov transform's sort key assumes a dict,
        # so coerce null to an empty dict before delegating.
        for record in data:
            if isinstance(record, dict) and record.get("latestAction") is None:
                record["latestAction"] = {}
        rows = CongressBillsFetcher.transform_data(query, data, **kwargs)
        return _within_update_window(rows, query.start_date, query.end_date)
