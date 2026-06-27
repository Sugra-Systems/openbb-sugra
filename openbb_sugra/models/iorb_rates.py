"""Sugra IORB (Interest Rate on Reserve Balances) Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.iorb_rates import (
    IORBData,
    IORBQueryParams,
)

# Single fixed FRED series: Interest Rate on Reserve Balances.
_SERIES_ID = "IORB"


class SugraIORBQueryParams(IORBQueryParams):
    """Sugra IORB Query Parameters."""


class SugraIORBData(IORBData):
    """Sugra IORB Data."""


class SugraIORBFetcher(Fetcher[SugraIORBQueryParams, list[SugraIORBData]]):
    """Fetch the Interest Rate on Reserve Balances (IORB) from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraIORBQueryParams:
        """Transform the query parameters."""
        return SugraIORBQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraIORBQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw IORB series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {"limit": 1000, "sort_order": "desc"}
        if query.start_date:
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        response = await sugra_get(f"/api/v1/fred/series/{_SERIES_ID}", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraIORBQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraIORBData]:
        """Validate into the standard model (IORB rate is an as-is percent)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows = fred_observations(data)
        if not rows:
            raise EmptyDataError("No IORB observations returned.")
        return [
            SugraIORBData.model_validate({"date": r["date"], "rate": r["value"]})
            for r in rows
        ]
