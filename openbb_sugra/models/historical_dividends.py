"""Sugra Historical Dividends Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.historical_dividends import (
    HistoricalDividendsData,
    HistoricalDividendsQueryParams,
)


def _parse_date(value: Any) -> dateType | None:
    """Parse a YYYY-MM-DD (or ISO) date string into a date."""
    # pylint: disable=import-outside-toplevel
    from datetime import datetime

    if not value:
        return None
    if isinstance(value, dateType):
        return value
    text = str(value)[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


class SugraHistoricalDividendsQueryParams(HistoricalDividendsQueryParams):
    """Sugra Historical Dividends Query Parameters."""


class SugraHistoricalDividendsData(HistoricalDividendsData):
    """Sugra Historical Dividends Data."""


class SugraHistoricalDividendsFetcher(
    Fetcher[
        SugraHistoricalDividendsQueryParams,
        list[SugraHistoricalDividendsData],
    ]
):
    """Fetch the historical dividend series from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraHistoricalDividendsQueryParams:
        """Transform the query parameters."""
        return SugraHistoricalDividendsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraHistoricalDividendsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw corporate actions from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v2/quotes/{query.symbol.upper()}/actions", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, list) else []

    @staticmethod
    def transform_data(
        query: SugraHistoricalDividendsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraHistoricalDividendsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        symbol = query.symbol.upper()
        out: list[SugraHistoricalDividendsData] = []
        for r in data:
            if (r.get("type") or "").lower() != "dividend":
                continue
            ex_date = _parse_date(r.get("date"))
            amount = r.get("amount")
            if ex_date is None or amount is None:
                continue
            if query.start_date and ex_date < query.start_date:
                continue
            if query.end_date and ex_date > query.end_date:
                continue
            out.append(
                SugraHistoricalDividendsData(
                    symbol=symbol,
                    ex_dividend_date=ex_date,
                    amount=amount,
                )
            )
        if not out:
            raise EmptyDataError("No historical dividends returned for the symbol.")
        return out
