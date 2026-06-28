"""Sugra Equity Fails-to-Deliver Model."""

# pylint: disable=unused-argument

from datetime import date
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_ftd import (
    EquityFtdData,
    EquityFtdQueryParams,
)


class SugraEquityFtdQueryParams(EquityFtdQueryParams):
    """Sugra Equity Fails-to-Deliver Query Parameters."""


class SugraEquityFtdData(EquityFtdData):
    """Sugra Equity Fails-to-Deliver Data."""


class SugraEquityFtdFetcher(
    Fetcher[SugraEquityFtdQueryParams, list[SugraEquityFtdData]]
):
    """Fetch SEC fails-to-deliver settlement history from the Sugra API.

    Sugra serves the SEC's twice-monthly fails-to-deliver dataset as a per-symbol
    timeseries at ``/api/v1/short-side/fails-to-deliver/{symbol}``. Each record is
    one settlement date with the failed-share quantity, prior-day close, CUSIP and
    security description - exactly the standard ``EquityFTD`` shape.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquityFtdQueryParams:
        """Transform the query parameters."""
        return SugraEquityFtdQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityFtdQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw fails-to-deliver records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        symbol = query.symbol.upper()
        response = await sugra_get(
            f"/api/v1/short-side/fails-to-deliver/{symbol}", api_key
        )
        payload = envelope_data(response)
        if not isinstance(payload, dict):
            return []
        # The rollup carries the canonical (resolved) symbol; prefer it over the
        # raw query value so an alias still labels rows with the real ticker.
        canonical = payload.get("symbol") or symbol
        rows: list[dict] = []
        for rec in payload.get("records") or []:
            if not isinstance(rec, dict) or not rec.get("date"):
                continue
            # The standard model's settlement_date validator runs strftime on the
            # value, so it must be a date object - the Sugra rollup stores it as an
            # ISO date string. Slice to the date portion (defensive against any
            # future time component, which date.fromisoformat rejects on 3.10) and
            # skip a malformed date rather than sink the whole pull.
            try:
                settlement_date = date.fromisoformat(str(rec["date"])[:10])
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "symbol": canonical,
                    "settlement_date": settlement_date,
                    "cusip": rec.get("cusip"),
                    "quantity": rec.get("quantity"),
                    "price": rec.get("price"),
                    "description": rec.get("description"),
                }
            )
        return rows

    @staticmethod
    def transform_data(
        query: SugraEquityFtdQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityFtdData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No fails-to-deliver data returned for the symbol.")
        return [SugraEquityFtdData.model_validate(d) for d in data]
