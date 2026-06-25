"""Sugra Congress Amendments Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_congress_gov.models.congress_amendments import (
    CongressAmendmentsData,
    CongressAmendmentsQueryParams,
)
from openbb_core.provider.abstract.fetcher import Fetcher


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
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

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
        """Validate and transform into the standard model.

        Sugra serves the congress.gov amendment shape; filtered responses carry
        the nested ``latestAction``/``amendedBill``/``sponsors`` objects, so the
        canonical congress.gov transform maps them faithfully. Per-amendment
        detail fields that the list view omits stay null, which the model allows.
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
        return CongressAmendmentsFetcher.transform_data(query, data, **kwargs)
