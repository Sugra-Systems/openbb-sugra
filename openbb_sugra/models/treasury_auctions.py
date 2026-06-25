"""Sugra US Treasury Auctions Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.treasury_auctions import (
    USTreasuryAuctionsData,
    USTreasuryAuctionsQueryParams,
)

# The standard model's security_type is lowercase; the Sugra endpoint (FiscalData)
# uses the canonical title/upper case.
_SECURITY_TYPE = {
    "bill": "Bill", "note": "Note", "bond": "Bond",
    "cmb": "CMB", "tips": "TIPS", "frn": "FRN",
}

# Sugra projection field -> standard model field, for the numeric columns that
# arrive as strings and need float coercion.
_FLOAT_MAP = {
    "high_yield": "high_yield",
    "bid_to_cover_ratio": "bid_to_cover_ratio",
    "offering_amt": "offering_amount",
    "total_accepted": "total_accepted",
    "allocation_pctage": "allocation_percentage",
}
# Fields whose names already match the standard model and pass through as-is.
_DIRECT = (
    "cusip", "issue_date", "security_type", "security_term", "maturity_date",
    "auction_date", "interest_rate", "original_security_term", "original_issue_date",
)


def _to_float(value: Any) -> float | None:
    """Coerce a numeric string to float; '', 'null', None -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s.lower() in ("null", "none", "n/a", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


class SugraUSTreasuryAuctionsFetcher(
    Fetcher[USTreasuryAuctionsQueryParams, list[USTreasuryAuctionsData]]
):
    """Fetch US Treasury auction results from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> USTreasuryAuctionsQueryParams:
        """Transform the query parameters."""
        return USTreasuryAuctionsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: USTreasuryAuctionsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw auction rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        # The Sugra endpoint paginates only by page size; it has no page offset,
        # so a page_num beyond the first cannot be honoured - reject rather than
        # silently returning page 1.
        if query.page_num is not None and query.page_num > 1:
            raise OpenBBError(
                "The Sugra treasury provider does not support page_num pagination; "
                "widen page_size instead."
            )

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.security_type is not None:
            params["security_type"] = _SECURITY_TYPE.get(
                query.security_type, query.security_type
            )
        if query.page_size is not None:
            params["limit"] = query.page_size
        response = await sugra_get("/api/v1/treasury/auctions", api_key, params)
        payload = envelope_data(response)
        return payload.get("records", []) if isinstance(payload, dict) else []

    @staticmethod
    def transform_data(
        query: USTreasuryAuctionsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[USTreasuryAuctionsData]:
        """Map to the standard model and apply client-side cusip/date filters.

        The Sugra endpoint does not filter by cusip or auction date server-side,
        so the standard model's cusip/start_date/end_date are applied here,
        bounded to the fetched page.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError
        from pydantic import ValidationError

        if not data:
            raise EmptyDataError("No US Treasury auction records returned.")

        wanted_cusip = (query.cusip or "").strip().upper() or None
        rows: list[USTreasuryAuctionsData] = []
        for rec in data:
            if not isinstance(rec, dict):
                continue
            # issue_date + maturity_date are required by the standard model; the
            # Sugra endpoint serves them, but skip a row that lacks either.
            if not rec.get("issue_date") or not rec.get("maturity_date"):
                continue
            mapped: dict[str, Any] = {
                k: rec[k] for k in _DIRECT if rec.get(k) is not None
            }
            for ours, std in _FLOAT_MAP.items():
                val = _to_float(rec.get(ours))
                if val is not None:
                    mapped[std] = val
            if rec.get("allocation_method"):
                mapped["auction_format"] = rec["allocation_method"]
            if wanted_cusip and str(mapped.get("cusip", "")).upper() != wanted_cusip:
                continue
            try:
                rows.append(USTreasuryAuctionsData.model_validate(mapped))
            except ValidationError:
                continue

        # Client-side auction-date window (the endpoint ignores start/end).
        start, end = query.start_date, query.end_date
        if start or end:
            rows = [
                r
                for r in rows
                if (start is None or (r.auction_date and r.auction_date >= start))
                and (end is None or (r.auction_date and r.auction_date <= end))
            ]

        if not rows:
            raise EmptyDataError("No US Treasury auction records matched the query.")
        return rows
