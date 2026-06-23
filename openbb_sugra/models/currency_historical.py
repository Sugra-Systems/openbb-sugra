"""Sugra Currency Historical Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.currency_historical import (
    CurrencyHistoricalData,
    CurrencyHistoricalQueryParams,
)


def _split_pair(symbol: str) -> tuple[str, str]:
    """Split a CURR1CURR2 / CURR1-CURR2 symbol into (base, quote)."""
    cleaned = symbol.upper().replace("-", "").replace("/", "")
    if len(cleaned) >= 6:
        return cleaned[:3], cleaned[3:6]
    # Fallback: treat the whole thing as the quote currency against EUR.
    return "EUR", cleaned


class SugraCurrencyHistoricalQueryParams(CurrencyHistoricalQueryParams):
    """Sugra Currency Historical Query Parameters."""


class SugraCurrencyHistoricalData(CurrencyHistoricalData):
    """Sugra Currency Historical Data.

    The Sugra forex history endpoint returns ECB end-of-day reference rates
    (EUR base). A requested pair is computed by cross-rating EUR-quoted rates,
    so each row carries a single `close` (the exchange rate) and no OHLCV.
    """


class SugraCurrencyHistoricalFetcher(
    Fetcher[SugraCurrencyHistoricalQueryParams, list[SugraCurrencyHistoricalData]]
):
    """Fetch a currency-pair rate series from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraCurrencyHistoricalQueryParams:
        """Transform the query parameters."""
        return SugraCurrencyHistoricalQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCurrencyHistoricalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw EUR-based rate rows from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from datetime import date as dateType

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        base, quote = _split_pair(query.symbol)

        wanted = {c for c in (base, quote) if c != "EUR"}
        params: dict[str, Any] = {}
        if wanted:
            params["symbols"] = ",".join(sorted(wanted))

        if query.start_date:
            end = query.end_date or dateType.today()
            span = max((end - query.start_date).days, 1)
            params["days"] = str(min(span + 5, 365))
        else:
            params["days"] = "30"

        response = await sugra_get("/api/v1/forex/history", api_key, params)
        payload = envelope_data(response)
        rows = payload if isinstance(payload, list) else []
        return [{"_base": base, "_quote": quote, **r} for r in rows]

    @staticmethod
    def transform_data(
        query: SugraCurrencyHistoricalQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCurrencyHistoricalData]:
        """Cross-rate the EUR rows into the requested pair and validate."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No currency history returned for the symbol.")

        results: list[SugraCurrencyHistoricalData] = []
        for row in data:
            base = row.get("_base")
            quote = row.get("_quote")
            rates = row.get("rates") or {}
            # EUR per 1 unit of each currency is 1/rate; rate is foreign per EUR.
            base_rate = 1.0 if base == "EUR" else rates.get(base)
            quote_rate = 1.0 if quote == "EUR" else rates.get(quote)
            if base_rate in (None, 0) or quote_rate is None:
                continue
            # base->quote = (foreign/EUR for quote) / (foreign/EUR for base)
            close = quote_rate / base_rate
            results.append(SugraCurrencyHistoricalData(date=row["date"], close=close))

        if query.start_date:
            results = [r for r in results if _as_date(r.date) >= query.start_date]
        if query.end_date:
            results = [r for r in results if _as_date(r.date) <= query.end_date]

        if not results:
            raise EmptyDataError("No currency history rows after filtering.")
        results.sort(key=lambda r: r.date)
        return results


def _as_date(value):
    """Return a date for a date or datetime value."""
    return value.date() if hasattr(value, "date") else value
