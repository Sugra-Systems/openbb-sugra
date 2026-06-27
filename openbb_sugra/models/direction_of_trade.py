"""Sugra Direction of Trade Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.direction_of_trade import (
    DirectionOfTradeData,
    DirectionOfTradeQueryParams,
)
from pydantic import Field


class SugraDirectionOfTradeQueryParams(DirectionOfTradeQueryParams):
    """Sugra Direction of Trade Query Parameters."""

    __json_schema_extra__ = {
        "country": {"multiple_items_allowed": True},
        "counterpart": {"multiple_items_allowed": True},
    }


class SugraDirectionOfTradeData(DirectionOfTradeData):
    """Sugra Direction of Trade Data."""

    country_code: str | None = Field(
        default=None, description="ISO code of the reporter country."
    )
    counterpart_code: str | None = Field(
        default=None, description="ISO code of the counterpart country."
    )
    unit: str | None = Field(default=None, description="Unit of the trade value.")
    unit_multiplier: int | None = Field(
        default=None,
        description="Multiplier (10^scale) describing the reporting scale; the value "
        "is already the whole figure, so this is metadata only.",
    )


class SugraDirectionOfTradeFetcher(
    Fetcher[SugraDirectionOfTradeQueryParams, list[SugraDirectionOfTradeData]]
):
    """Fetch IMF Direction of Trade (bilateral goods trade) from the Sugra API.

    Backed by /api/v1/imf/direction-of-trade, which queries the public IMF SDMX
    3.0 IMTS dataflow server-side (one bounded call, cached 24h). Values are the
    raw trade figures in USD. Source: International Monetary Fund, Direction of
    Trade Statistics.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraDirectionOfTradeQueryParams:
        """Transform the query parameters."""
        return SugraDirectionOfTradeQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraDirectionOfTradeQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw direction-of-trade payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import OpenBBError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        # None means "all" on each side, but both-"all" is the full IMTS matrix and
        # is rejected. Surface a clear error instead of a bare upstream 422.
        if not query.country and not query.counterpart:
            raise OpenBBError(
                "Specify at least one of 'country' or 'counterpart' "
                "(both cannot be 'all')."
            )
        api_key = get_api_key(credentials)
        params: dict[str, Any] = {
            "country": query.country or "all",
            "counterpart": query.counterpart or "all",
            "direction": query.direction,
            "frequency": query.frequency,
        }
        if query.start_date:
            params["start_date"] = str(query.start_date)
        if query.end_date:
            params["end_date"] = str(query.end_date)
        response = await sugra_get("/api/v1/imf/direction-of-trade", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraDirectionOfTradeQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraDirectionOfTradeData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        results = (data or {}).get("results") or []
        if not results:
            raise EmptyDataError("No direction of trade data returned.")
        return [
            SugraDirectionOfTradeData.model_validate(r)
            for r in results
            if isinstance(r, dict)
        ]
