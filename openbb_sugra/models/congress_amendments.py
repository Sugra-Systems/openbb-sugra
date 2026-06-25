"""Sugra Congress Amendments Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_congress_gov.models.congress_amendments import (
    CongressAmendmentsData,
    CongressAmendmentsQueryParams,
)
from openbb_core.provider.abstract.fetcher import Fetcher

from openbb_sugra.models.congress_bills import _within_update_window


class SugraCongressAmendmentsFetcher(
    Fetcher[CongressAmendmentsQueryParams, list[CongressAmendmentsData]]
):
    """List current and historical U.S. Congressional amendments from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> CongressAmendmentsQueryParams:
        """Transform the query parameters."""
        return CongressAmendmentsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: CongressAmendmentsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw amendment list from the Sugra API."""
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
        if query.amendment_type is not None:
            params["amendment_type"] = query.amendment_type
        if query.limit is not None:
            params["limit"] = query.limit
        response = await sugra_get("/api/v1/congress/amendments", api_key, params)
        payload = envelope_data(response)
        return payload.get("amendments", []) if isinstance(payload, dict) else []

    @staticmethod
    def transform_data(
        query: CongressAmendmentsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[CongressAmendmentsData]:
        """Validate, transform, and apply client-side filters.

        Sugra serves the congress.gov amendment LIST shape (congress, number,
        type, update date, url); the canonical congress.gov transform maps it,
        and the per-amendment detail fields (amended_bill, sponsor, purpose,
        submitted_date) it normally enriches via extra HTTP calls are NOT present
        in the Sugra list response, so they stay null. The Sugra endpoint also
        ignores amendment_type and start_date/end_date, so both are applied
        client-side here (bounded to the fetched page).
        """
        # pylint: disable=import-outside-toplevel
        from openbb_congress_gov.models.congress_amendments import (
            CongressAmendmentsFetcher,
        )
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No Congressional amendments returned.")
        # Sugra may emit `latestAction: null`; the congress.gov transform's sort
        # key assumes a dict, so coerce null to an empty dict before delegating.
        for record in data:
            if isinstance(record, dict) and record.get("latestAction") is None:
                record["latestAction"] = {}
        rows = CongressAmendmentsFetcher.transform_data(query, data, **kwargs)
        # The Sugra amendments endpoint ignores the type filter, so apply it here.
        if query.amendment_type:
            wanted = query.amendment_type.lower()
            rows = [r for r in rows if (r.amendment_type or "").lower() == wanted]
        return _within_update_window(rows, query.start_date, query.end_date)
