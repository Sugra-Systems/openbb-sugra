"""Sugra Options Chains Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from datetime import datetime, timezone
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.options_chains import (
    OptionsChainsData,
    OptionsChainsQueryParams,
)
from pydantic import Field


class SugraOptionsChainsQueryParams(OptionsChainsQueryParams):
    """Sugra Options Chains Query Parameters."""

    expiration: str | None = Field(
        default=None,
        description=(
            "Specific expiration date (YYYY-MM-DD) to retrieve contracts for."
            " If omitted, the nearest available expiration is used."
        ),
    )


class SugraOptionsChainsData(OptionsChainsData):
    """Sugra Options Chains Data."""


def _epoch_to_dt(value: Any) -> datetime | None:
    """Convert an epoch-seconds value to an aware datetime, or pass through."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    return None


class SugraOptionsChainsFetcher(Fetcher[SugraOptionsChainsQueryParams, SugraOptionsChainsData]):
    """Fetch an options chain from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraOptionsChainsQueryParams:
        """Transform the query parameters."""
        return SugraOptionsChainsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraOptionsChainsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw options chain for a single expiration from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        symbol = query.symbol.upper()

        expiration = query.expiration
        if not expiration:
            # Resolve the nearest expiration from the chain index endpoint.
            index = await sugra_get(f"/api/v2/quotes/{symbol}/options", api_key)
            index_payload = envelope_data(index)
            expirations = (
                index_payload.get("expirations", []) if isinstance(index_payload, dict) else []
            )
            if not expirations:
                return {}
            expiration = expirations[0]

        response = await sugra_get(f"/api/v2/quotes/{symbol}/options/{expiration}", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraOptionsChainsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> SugraOptionsChainsData:
        """Flatten calls/puts into the columnar standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        symbol = query.symbol.upper()
        expiration_str = (data or {}).get("expiration")
        calls = (data or {}).get("calls") or []
        puts = (data or {}).get("puts") or []
        if not calls and not puts:
            raise EmptyDataError("No options chain contracts returned.")

        exp_date = datetime.strptime(expiration_str, "%Y-%m-%d").date() if expiration_str else None
        today = dateType.today()

        cols: dict[str, list] = {
            "underlying_symbol": [],
            "contract_symbol": [],
            "expiration": [],
            "dte": [],
            "strike": [],
            "option_type": [],
            "contract_size": [],
            "open_interest": [],
            "volume": [],
            "last_trade_price": [],
            "last_trade_time": [],
            "bid": [],
            "ask": [],
            "implied_volatility": [],
            "change": [],
            "change_percent": [],
        }

        def add(contract: dict, opt_type: str) -> None:
            cols["underlying_symbol"].append(symbol)
            cols["contract_symbol"].append(contract.get("contractSymbol"))
            cols["expiration"].append(exp_date)
            cols["dte"].append((exp_date - today).days if exp_date else None)
            cols["strike"].append(contract.get("strike"))
            cols["option_type"].append(opt_type)
            size = contract.get("contractSize")
            cols["contract_size"].append(100 if size == "REGULAR" else None)
            cols["open_interest"].append(contract.get("openInterest"))
            cols["volume"].append(contract.get("volume"))
            cols["last_trade_price"].append(contract.get("lastPrice"))
            cols["last_trade_time"].append(contract.get("lastTradeDate"))
            cols["bid"].append(contract.get("bid"))
            cols["ask"].append(contract.get("ask"))
            cols["implied_volatility"].append(contract.get("impliedVolatility"))
            cols["change"].append(contract.get("change"))
            cols["change_percent"].append(contract.get("percentChange"))

        for c in calls:
            add(c, "call")
        for p in puts:
            add(p, "put")

        return SugraOptionsChainsData.model_validate(cols)
