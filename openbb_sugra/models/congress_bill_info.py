"""Sugra Congress Bill Info Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_congress_gov.models.bill_info import (
    CongressBillInfoData,
    CongressBillInfoQueryParams,
)
from openbb_core.provider.abstract.fetcher import Fetcher


def _parse_bill_ref(bill_ref: str) -> tuple[int, str, str]:
    """Resolve a bill URL, V4 slash ref, or V5 id to congress/type/number.

    Accepts ``119/hr/1``, ``119-hr-1``, optionally leading-slashed, or a full
    congress.gov URL like ``https://api.congress.gov/v3/bill/119/s/1947``.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_core.app.model.abstract.error import OpenBBError

    ref = (bill_ref or "").strip()
    if ref.lower().startswith("http"):
        from urllib.parse import urlparse

        parts = [p for p in urlparse(ref).path.split("/") if p]
        seg = parts[parts.index("bill") + 1:][:3] if "bill" in parts else parts[-3:]
    elif "/" not in ref and "-" in ref:
        seg = [p for p in ref.split("-") if p]
    else:
        seg = [p for p in ref.strip("/").split("/") if p]
    if len(seg) < 3:
        raise OpenBBError(
            f"Could not parse a bill reference from '{bill_ref}'. Expected "
            "'congress/type/number', 'congress-type-number', or a full bill URL."
        )
    congress, bill_type, number = seg[0], seg[1], seg[2]
    try:
        return int(congress), bill_type.lower(), str(number)
    except (TypeError, ValueError) as exc:
        raise OpenBBError(
            f"Invalid congress number in bill reference '{bill_ref}'."
        ) from exc


def _bill_id(congress: int, bill_type: str, number: str) -> str:
    """Return the OpenBB V5 bill id."""
    return f"{congress}-{bill_type.lower()}-{number}"


def _bill_url(congress: int, bill_type: str, number: str) -> str:
    """Return the OpenBB V4 slash-style bill reference."""
    return f"{congress}/{bill_type.lower()}/{number}"


def _query_bill_ref(query: CongressBillInfoQueryParams) -> str:
    """Return the bill reference from either V4 or V5 query models."""
    return getattr(query, "bill_url", None) or getattr(query, "bill_id")


class SugraCongressBillInfoFetcher(
    Fetcher[CongressBillInfoQueryParams, CongressBillInfoData]
):
    """Full metadata and summary for a single U.S. Congressional bill via the Sugra API.

    The Sugra bill endpoint inlines all seven sub-resources server-side
    (``?expand=all``, paginated to the full arrays), so this fetcher makes ONE
    Sugra call in place of the standard provider's eight congress.gov round-trips,
    then reuses the canonical markdown builder verbatim - the output is identical
    to the standard provider's, but built from the complete (not first-page) arrays.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> CongressBillInfoQueryParams:
        """Transform the query parameters."""
        normalized = dict(params)
        fields = CongressBillInfoQueryParams.model_fields
        if "bill_id" in fields and "bill_id" not in normalized:
            ref = normalized.pop("bill_url", None)
            if ref is not None:
                normalized["bill_id"] = _bill_id(*_parse_bill_ref(ref))
        elif "bill_url" in fields and "bill_url" not in normalized:
            ref = normalized.pop("bill_id", None)
            if ref is not None:
                normalized["bill_url"] = _bill_url(*_parse_bill_ref(ref))
        return CongressBillInfoQueryParams(**normalized)

    @staticmethod
    async def aextract_data(
        query: CongressBillInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the fully-expanded bill record from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        congress, bill_type, number = _parse_bill_ref(_query_bill_ref(query))
        response = await sugra_get(
            f"/api/v1/congress/bills/{congress}/{bill_type}/{number}",
            api_key,
            {"expand": "all"},
        )
        bill = envelope_data(response)
        if not isinstance(bill, dict) or not bill:
            raise EmptyDataError(
                f"No bill found for {congress}/{bill_type}/{number}."
            )
        return bill

    @staticmethod
    def transform_data(
        query: CongressBillInfoQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> CongressBillInfoData:
        """Build the markdown record via the canonical congress.gov transform.

        Sugra serves the same congress.gov bill shape with the sub-resources
        already spliced in (the standard provider splices them client-side), so
        the canonical transform yields an identical CongressBillInfoData.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_congress_gov.models.bill_info import CongressBillInfoFetcher
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No bill information returned.")
        return CongressBillInfoFetcher.transform_data(query, data, **kwargs)
