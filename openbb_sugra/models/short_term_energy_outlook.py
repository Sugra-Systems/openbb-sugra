"""Sugra Short Term Energy Outlook Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.short_term_energy_outlook import (
    ShortTermEnergyOutlookData,
    ShortTermEnergyOutlookQueryParams,
)


def _parse_month(value: Any) -> dateType | None:
    """Parse a YYYY-MM (or YYYY-MM-DD) string into a date at the first of the month."""
    # pylint: disable=import-outside-toplevel
    from datetime import datetime

    if not value:
        return None
    if isinstance(value, dateType):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


class SugraShortTermEnergyOutlookQueryParams(ShortTermEnergyOutlookQueryParams):
    """Sugra Short Term Energy Outlook Query Parameters."""


class SugraShortTermEnergyOutlookData(ShortTermEnergyOutlookData):
    """Sugra Short Term Energy Outlook Data."""


class SugraShortTermEnergyOutlookFetcher(
    Fetcher[
        SugraShortTermEnergyOutlookQueryParams,
        list[SugraShortTermEnergyOutlookData],
    ]
):
    """Fetch the EIA Short Term Energy Outlook from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraShortTermEnergyOutlookQueryParams:
        """Transform the query parameters."""
        return SugraShortTermEnergyOutlookQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraShortTermEnergyOutlookQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw Short Term Energy Outlook payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/commodities/energy/steo", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraShortTermEnergyOutlookQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraShortTermEnergyOutlookData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        rows = data.get("rows") if isinstance(data, dict) else None
        if not rows:
            raise EmptyDataError("No Short Term Energy Outlook data returned.")

        table = data.get("dataset")
        out: list[SugraShortTermEnergyOutlookData] = []
        for order, record in enumerate(rows):
            obs_date = _parse_month(record.get("date"))
            value = record.get("value")
            symbol = record.get("symbol")
            if obs_date is None or value is None or not symbol:
                continue
            if query.start_date and obs_date < query.start_date:
                continue
            if query.end_date and obs_date > query.end_date:
                continue
            out.append(
                SugraShortTermEnergyOutlookData(
                    date=obs_date,
                    table=table,
                    symbol=symbol,
                    order=order,
                    title=record.get("title"),
                    value=value,
                    unit=record.get("unit"),
                )
            )
        if not out:
            raise EmptyDataError("No Short Term Energy Outlook data returned.")
        return out
