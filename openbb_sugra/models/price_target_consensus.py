"""Sugra Price Target Consensus Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.price_target_consensus import (
    PriceTargetConsensusData,
    PriceTargetConsensusQueryParams,
)
from pydantic import Field


class SugraPriceTargetConsensusQueryParams(PriceTargetConsensusQueryParams):
    """Sugra Price Target Consensus Query Parameters."""


class SugraPriceTargetConsensusData(PriceTargetConsensusData):
    """Sugra Price Target Consensus Data."""

    current_price: float | None = Field(
        default=None, description="Current price at the time of the consensus."
    )
    number_of_analysts: int | None = Field(
        default=None, description="Number of analysts in the consensus."
    )
    recommendation: str | None = Field(
        default=None, description="Consensus recommendation (e.g. buy, hold, sell)."
    )


class SugraPriceTargetConsensusFetcher(
    Fetcher[
        SugraPriceTargetConsensusQueryParams,
        list[SugraPriceTargetConsensusData],
    ]
):
    """Fetch the analyst price-target consensus from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraPriceTargetConsensusQueryParams:
        """Transform the query parameters."""
        return SugraPriceTargetConsensusQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraPriceTargetConsensusQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw analyst-targets payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        if not query.symbol:
            raise ValueError("Symbol is required for price target consensus.")
        api_key = get_api_key(credentials)
        response = await sugra_get(
            f"/api/v2/quotes/{query.symbol.upper()}/analyst-targets", api_key
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraPriceTargetConsensusQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraPriceTargetConsensusData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data or data.get("mean") is None and data.get("median") is None:
            raise EmptyDataError("No price target consensus returned for the symbol.")

        return [
            SugraPriceTargetConsensusData(
                symbol=(query.symbol or "").upper(),
                target_high=data.get("high"),
                target_low=data.get("low"),
                target_consensus=data.get("mean"),
                target_median=data.get("median"),
                current_price=data.get("current"),
                number_of_analysts=data.get("number_of_analysts"),
                recommendation=data.get("recommendation"),
            )
        ]
