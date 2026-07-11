"""Sugra Congress Amendment Info Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_congress_gov.models.amendment_info import (
    CongressAmendmentInfoData,
    CongressAmendmentInfoQueryParams,
)
from openbb_core.provider.abstract.fetcher import Fetcher


def _parse_amendment_ref(amendment_ref: str) -> tuple[int, str, str]:
    """Resolve an amendment URL, V4 slash ref, or V5 id.

    Accepts ``119/hamdt/2``, ``119-hamdt-2``, optionally leading-slashed, or a
    full congress.gov URL like ``https://api.congress.gov/v3/amendment/119/hamdt/2``.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_core.app.model.abstract.error import OpenBBError

    ref = (amendment_ref or "").strip()
    if ref.lower().startswith("http"):
        from urllib.parse import urlparse

        parts = [p for p in urlparse(ref).path.split("/") if p]
        seg = (
            parts[parts.index("amendment") + 1:][:3]
            if "amendment" in parts
            else parts[-3:]
        )
    elif "/" not in ref and "-" in ref:
        seg = [p for p in ref.split("-") if p]
    else:
        seg = [p for p in ref.strip("/").split("/") if p]
    if len(seg) < 3:
        raise OpenBBError(
            f"Could not parse an amendment reference from '{amendment_ref}'. Expected "
            "'congress/type/number', 'congress-type-number', or a full amendment URL."
        )
    congress, amendment_type, number = seg[0], seg[1], seg[2]
    try:
        return int(congress), amendment_type.lower(), str(number)
    except (TypeError, ValueError) as exc:
        raise OpenBBError(
            f"Invalid congress number in amendment reference '{amendment_ref}'."
        ) from exc


def _amendment_id(congress: int, amendment_type: str, number: str) -> str:
    """Return the OpenBB V5 amendment id."""
    return f"{congress}-{amendment_type.lower()}-{number}"


def _amendment_url(congress: int, amendment_type: str, number: str) -> str:
    """Return the OpenBB V4 slash-style amendment reference."""
    return f"{congress}/{amendment_type.lower()}/{number}"


def _query_amendment_ref(query: CongressAmendmentInfoQueryParams) -> str:
    """Return the amendment reference from either V4 or V5 query models."""
    return getattr(query, "amendment_url", None) or getattr(query, "amendment_id")


class SugraCongressAmendmentInfoFetcher(
    Fetcher[CongressAmendmentInfoQueryParams, CongressAmendmentInfoData]
):
    """Full metadata and detail for a single U.S. Congressional amendment via the Sugra API.

    The Sugra amendment endpoint inlines the cosponsors / actions / text sub-resources
    server-side (``?expand=all``, paginated to the full arrays), so this fetcher makes
    ONE Sugra call in place of the standard provider's per-sub-resource congress.gov
    round-trips, then reuses the canonical markdown builder verbatim.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> CongressAmendmentInfoQueryParams:
        """Transform the query parameters."""
        normalized = dict(params)
        fields = CongressAmendmentInfoQueryParams.model_fields
        if "amendment_id" in fields and "amendment_id" not in normalized:
            ref = normalized.pop("amendment_url", None)
            if ref is not None:
                normalized["amendment_id"] = _amendment_id(
                    *_parse_amendment_ref(ref)
                )
        elif "amendment_url" in fields and "amendment_url" not in normalized:
            ref = normalized.pop("amendment_id", None)
            if ref is not None:
                normalized["amendment_url"] = _amendment_url(
                    *_parse_amendment_ref(ref)
                )
        return CongressAmendmentInfoQueryParams(**normalized)

    @staticmethod
    async def aextract_data(
        query: CongressAmendmentInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the fully-expanded amendment record from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        congress, amendment_type, number = _parse_amendment_ref(
            _query_amendment_ref(query)
        )
        response = await sugra_get(
            f"/api/v1/congress/amendments/{congress}/{amendment_type}/{number}",
            api_key,
            {"expand": "all"},
        )
        amendment = envelope_data(response)
        if not isinstance(amendment, dict) or not amendment:
            raise EmptyDataError(
                f"No amendment found for {congress}/{amendment_type}/{number}."
            )
        return amendment

    @staticmethod
    def transform_data(
        query: CongressAmendmentInfoQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> CongressAmendmentInfoData:
        """Build the markdown record via the canonical congress.gov transform.

        Sugra serves the same congress.gov amendment shape with the sub-resources
        already spliced in (the standard provider splices them client-side), so the
        canonical transform yields an identical CongressAmendmentInfoData.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_congress_gov.models.amendment_info import CongressAmendmentInfoFetcher
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No amendment information returned.")
        return CongressAmendmentInfoFetcher.transform_data(query, data, **kwargs)
