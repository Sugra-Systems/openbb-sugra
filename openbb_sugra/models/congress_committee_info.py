"""Sugra Congress Committee Info Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_congress_gov.models.congress_committee_info import (
    CongressCommitteeInfoData,
    CongressCommitteeInfoQueryParams,
)
from openbb_core.provider.abstract.fetcher import Fetcher


def _normalize_committee_detail(data: dict) -> dict:
    """Fill V5 committee detail aliases while preserving the Sugra payload."""
    if not isinstance(data, dict):
        return data
    normalized = dict(data)
    detail = normalized.get("detail")
    if not isinstance(detail, dict):
        return normalized

    detail = dict(detail)
    if not detail.get("name"):
        history = detail.get("history")
        if isinstance(history, list) and history:
            first_history = history[0]
            if isinstance(first_history, dict):
                detail["name"] = first_history.get("officialName")
    if not detail.get("chamber") and normalized.get("chamber"):
        detail["chamber"] = normalized["chamber"]
    if not detail.get("website") and detail.get("committeeWebsiteUrl"):
        detail["website"] = detail["committeeWebsiteUrl"]
    normalized["detail"] = detail
    return normalized


class SugraCongressCommitteeInfoFetcher(
    Fetcher[CongressCommitteeInfoQueryParams, CongressCommitteeInfoData]
):
    """Detail and current member roster for a single U.S. Congressional committee via the Sugra API.

    congress.gov exposes committee detail but carries NO member roster, so the
    standard provider makes a congress.gov detail call AND a second fetch of the
    @unitedstates ``committee-membership-current.json`` roster. The Sugra committee
    endpoint joins both server-side (systemCode -> thomas_id, shared-cached roster
    feed with stale-fallback) and returns the same ``{chamber, system_code, detail,
    members}`` shape, so this fetcher makes ONE Sugra call in place of the standard
    provider's two upstream round-trips, then reuses the canonical markdown builder
    verbatim - the output is identical to the standard provider's.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> CongressCommitteeInfoQueryParams:
        """Transform the query parameters."""
        return CongressCommitteeInfoQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: CongressCommitteeInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the combined committee detail + member roster from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        chamber = query.chamber.lower()
        system_code = (query.subcommittee or query.committee).lower()
        response = await sugra_get(
            f"/api/v1/congress/committees/{chamber}/{system_code}",
            api_key,
        )
        committee = envelope_data(response)
        if not isinstance(committee, dict) or not committee:
            raise EmptyDataError(
                f"No committee found for {chamber}/{system_code}."
            )
        return committee

    @staticmethod
    def transform_data(
        query: CongressCommitteeInfoQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> CongressCommitteeInfoData:
        """Build the markdown record via the canonical congress.gov transform.

        Sugra serves the same ``{chamber, system_code, detail, members}`` shape the
        standard provider assembles from its two upstream calls, so the canonical
        transform yields an identical CongressCommitteeInfoData.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_congress_gov.models.congress_committee_info import (
            CongressCommitteeInfoFetcher,
        )
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No committee information returned.")
        normalized = _normalize_committee_detail(data)
        return CongressCommitteeInfoFetcher.transform_data(query, normalized, **kwargs)
