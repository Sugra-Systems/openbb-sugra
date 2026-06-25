"""Sugra Congress Bills Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_congress_gov.models.congress_bills import (
    CongressBillsData,
    CongressBillsQueryParams,
)
from openbb_core.provider.abstract.fetcher import Fetcher


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
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

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
        """Validate and transform into the standard model.

        Sugra serves the congress.gov bill shape verbatim (including the nested
        ``latestAction`` object, present once filters are applied), so the
        canonical congress.gov transform maps it faithfully with no divergence.
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
        return CongressBillsFetcher.transform_data(query, data, **kwargs)
