"""Sugra Equity Screener Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_screener import (
    EquityScreenerData,
    EquityScreenerQueryParams,
)
from pydantic import Field, model_validator


class SugraEquityScreenerQueryParams(EquityScreenerQueryParams):
    """Sugra Equity Screener Query Parameters."""

    market_cap_min: float | None = Field(
        default=10_000_000_000,
        description="Minimum intraday market capitalization filter.",
    )
    region: str = Field(
        default="us",
        description="Region to screen.",
    )
    limit: int = Field(
        default=25,
        description="Maximum number of records to return.",
    )


class SugraEquityScreenerData(EquityScreenerData):
    """Sugra Equity Screener Data."""

    price: float | None = Field(default=None, description="Last price.")
    change: float | None = Field(default=None, description="Change in price.")
    change_percent: float | None = Field(default=None, description="Percent change in price.")
    volume: int | None = Field(default=None, description="Trading volume.")
    market_cap: float | None = Field(default=None, description="Market capitalization.")

    @model_validator(mode="before")
    @classmethod
    def _map_fields(cls, values):
        """Map a Sugra screener record onto the standard screener fields."""
        if not isinstance(values, dict):
            return values
        v = dict(values)
        out = {
            "symbol": v.get("symbol"),
            "name": v.get("name"),
            "price": v.get("price"),
            "change": v.get("change"),
            "change_percent": v.get("change_pct"),
            "volume": v.get("volume"),
            "market_cap": v.get("market_cap"),
        }
        return {k: val for k, val in out.items() if val is not None}


class SugraEquityScreenerFetcher(
    Fetcher[SugraEquityScreenerQueryParams, list[SugraEquityScreenerData]]
):
    """Run a custom equity screen via the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraEquityScreenerQueryParams:
        """Transform the query parameters."""
        return SugraEquityScreenerQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraEquityScreenerQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw screener records from the Sugra API (POST)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.helpers import amake_request

        from openbb_sugra.utils.helpers import (
            SUGRA_BASE_URL,
            envelope_data,
            get_api_key,
        )

        api_key = get_api_key(credentials)
        # The upstream custom screener expects a nested-operand format:
        # region as an EQ/OR group, plus comparison operands under a top-level AND.
        operands: list = [
            {
                "operator": "or",
                "operands": [{"operator": "EQ", "operands": ["region", query.region]}],
            }
        ]
        if query.market_cap_min is not None:
            operands.append(
                {"operator": "gt", "operands": ["intradaymarketcap", query.market_cap_min]}
            )
        body = {
            "query": {"operator": "AND", "operands": operands},
            "offset": 0,
            "size": query.limit,
            "sortField": "intradaymarketcap",
            "sortType": "DESC",
            "quoteType": "EQUITY",
        }
        url = f"{SUGRA_BASE_URL}/api/v2/market/screener"
        headers = {
            "x-api-key": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response = await amake_request(url, method="POST", headers=headers, json=body)
        payload = envelope_data(response)
        records = payload.get("records", []) if isinstance(payload, dict) else []
        return [r for r in records if isinstance(r, dict) and r.get("symbol")]

    @staticmethod
    def transform_data(
        query: SugraEquityScreenerQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraEquityScreenerData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No screener results returned.")
        return [SugraEquityScreenerData.model_validate(d) for d in data]
