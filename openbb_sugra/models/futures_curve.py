"""Sugra Futures Curve Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.futures_curve import (
    FuturesCurveData,
    FuturesCurveQueryParams,
)
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import Field


class SugraFuturesCurveQueryParams(FuturesCurveQueryParams):
    """Sugra Futures Curve Query Parameters."""

    max_contracts: int | None = Field(
        default=None,
        description="Maximum number of consecutive expirations to return (default 12).",
        ge=1,
        le=36,
    )


class SugraFuturesCurveData(FuturesCurveData):
    """Sugra Futures Curve Data."""


class SugraFuturesCurveFetcher(
    Fetcher[SugraFuturesCurveQueryParams, list[SugraFuturesCurveData]]
):
    """Fetch the futures term structure from the Sugra API.

    Backed by `/api/v2/futures/{root}/curve`. `symbol` is the futures root
    (e.g. CL, GC, ES). Returns the latest term-structure snapshot: one price per
    consecutive expiration.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraFuturesCurveQueryParams:
        """Transform the query parameters."""
        return SugraFuturesCurveQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraFuturesCurveQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw curve payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        if query.date is not None:
            # The Sugra curve is a latest snapshot; never silently ignore a date.
            raise OpenBBError(
                "The Sugra futures curve returns the latest snapshot; a historical"
                " 'date' is not supported."
            )

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.max_contracts:
            params["max_contracts"] = query.max_contracts

        response = await sugra_get(
            f"/api/v2/futures/{query.symbol}/curve", api_key, params
        )
        payload = envelope_data(response)
        if not isinstance(payload, dict) or not payload.get("points"):
            raise EmptyDataError()
        return payload

    @staticmethod
    def transform_data(
        query: SugraFuturesCurveQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraFuturesCurveData]:
        """Map the curve points to the standard model."""
        as_of = data.get("as_of")
        snapshot_date = as_of[:10] if isinstance(as_of, str) and len(as_of) >= 10 else None
        results: list[SugraFuturesCurveData] = []
        for point in data.get("points", []):
            expiration = point.get("expiration")
            price = point.get("price")
            # `expiration` (str) and `price` (float) are both required by the model.
            if not expiration or price is None:
                continue
            results.append(
                SugraFuturesCurveData.model_validate(
                    {
                        "date": snapshot_date,
                        "expiration": expiration,
                        "price": price,
                    }
                )
            )
        if not results:
            raise EmptyDataError()
        return results
