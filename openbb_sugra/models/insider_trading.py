"""Sugra Insider Trading Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.insider_trading import (
    InsiderTradingData,
    InsiderTradingQueryParams,
)
from pydantic import Field


class SugraInsiderTradingQueryParams(InsiderTradingQueryParams):
    """Sugra Insider Trading Query Parameters."""


class SugraInsiderTradingData(InsiderTradingData):
    """Sugra Insider Trading Data."""

    transaction_value: float | None = Field(
        default=None, description="Reported value of the transaction."
    )


class SugraInsiderTradingFetcher(
    Fetcher[SugraInsiderTradingQueryParams, list[SugraInsiderTradingData]]
):
    """Fetch insider transactions from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraInsiderTradingQueryParams:
        """Transform the query parameters."""
        return SugraInsiderTradingQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraInsiderTradingQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw insider transactions from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(
            f"/api/v2/quotes/{query.symbol.upper()}/insider-transactions", api_key
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, list) else []

    @staticmethod
    def transform_data(
        query: SugraInsiderTradingQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraInsiderTradingData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No insider transactions returned for the symbol.")

        symbol = query.symbol.upper()
        rows = data[: query.limit] if query.limit else data
        out: list[SugraInsiderTradingData] = []
        for r in rows:
            out.append(
                SugraInsiderTradingData(
                    symbol=symbol,
                    transaction_date=r.get("start_date"),
                    owner_name=r.get("insider"),
                    owner_title=r.get("position"),
                    ownership_type=r.get("ownership"),
                    transaction_type=(r.get("transaction") or None),
                    securities_transacted=r.get("shares"),
                    transaction_value=r.get("value"),
                )
            )
        return out
