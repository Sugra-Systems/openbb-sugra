"""Sugra Congress Committee Documents Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_congress_gov.models.congress_committee_documents import (
    CongressCommitteeDocumentsData,
    CongressCommitteeDocumentsQueryParams,
)
from openbb_core.provider.abstract.fetcher import Fetcher


class SugraCongressCommitteeDocumentsFetcher(
    Fetcher[CongressCommitteeDocumentsQueryParams, list[CongressCommitteeDocumentsData]]
):
    """A committee's document catalog via the Sugra API.

    The Sugra committee-documents endpoint serves the two committee-scoped legs -
    `report` and `legislation` - as structured rows ({doc_type, citation, title,
    congress, chamber, doc_url}), built server-side from congress.gov. This fetcher
    makes ONE Sugra call and delegates the canonical transform.

    LEAN-BUILD NOTE: the Sugra endpoint omits the chamber-wide `hearing` / `meeting`
    / `publication` legs the standard provider also assembles (a faithful build is a
    hundreds-of-calls fan-out that does not fit Sugra's single-worker model). The
    omission is disclosed on the Sugra response (`partial`/`skipped`); at the OpenBB
    layer it means `doc_type` `all` returns reports + legislation only, and an
    unsupported `doc_type` (meeting/publication) returns no rows. `report` and
    `legislation` are complete.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> CongressCommitteeDocumentsQueryParams:
        """Transform the query parameters."""
        return CongressCommitteeDocumentsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: CongressCommitteeDocumentsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Return the committee's document rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        chamber = query.chamber.lower()
        system_code = (query.subcommittee or query.committee).lower()
        params: dict[str, Any] = {
            "doc_type": query.doc_type,
            "limit": query.limit,
            "offset": query.offset,
        }
        if query.congress is not None:
            params["congress"] = query.congress
        response = await sugra_get(
            f"/api/v1/congress/committees/{chamber}/{system_code}/documents",
            api_key,
            params,
        )
        payload = envelope_data(response)
        return payload.get("documents", []) if isinstance(payload, dict) else []

    @staticmethod
    def transform_data(
        query: CongressCommitteeDocumentsQueryParams,
        data: list,
        **kwargs: Any,
    ) -> list[CongressCommitteeDocumentsData]:
        """Build the document rows via the canonical congress.gov transform.

        Sugra serves the same per-row shape the standard provider emits (doc_url
        rides along via the model's extra="allow"), so the canonical transform
        yields identical CongressCommitteeDocumentsData rows.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_congress_gov.models.congress_committee_documents import (
            CongressCommitteeDocumentsFetcher,
        )
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No committee documents returned.")
        return CongressCommitteeDocumentsFetcher.transform_data(query, data, **kwargs)
