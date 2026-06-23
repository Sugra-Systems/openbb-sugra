"""Sugra Institutional Ownership Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.institutional_ownership import (
    InstitutionalOwnershipData,
    InstitutionalOwnershipQueryParams,
)
from pydantic import Field


class SugraInstitutionalOwnershipQueryParams(InstitutionalOwnershipQueryParams):
    """Sugra Institutional Ownership Query Parameters."""


class SugraInstitutionalOwnershipData(InstitutionalOwnershipData):
    """Sugra Institutional Ownership Data."""

    holder: str | None = Field(default=None, description="Name of the institutional holder.")
    shares: float | None = Field(default=None, description="Number of shares held.")
    value: float | None = Field(default=None, description="Reported market value of the holding.")
    pct_held: float | None = Field(
        default=None, description="Percentage of shares outstanding held."
    )
    pct_change: float | None = Field(
        default=None, description="Change in holding since the prior report."
    )


class SugraInstitutionalOwnershipFetcher(
    Fetcher[
        SugraInstitutionalOwnershipQueryParams,
        list[SugraInstitutionalOwnershipData],
    ]
):
    """Fetch institutional holders from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraInstitutionalOwnershipQueryParams:
        """Transform the query parameters."""
        return SugraInstitutionalOwnershipQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraInstitutionalOwnershipQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw institutional holders payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(
            f"/api/v2/quotes/{query.symbol.upper()}/holders/institutional", api_key
        )
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraInstitutionalOwnershipQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraInstitutionalOwnershipData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        holders = data.get("holders", []) if isinstance(data, dict) else []
        if not holders:
            raise EmptyDataError("No institutional holders returned for the symbol.")

        symbol = query.symbol.upper()
        out: list[SugraInstitutionalOwnershipData] = []
        for h in holders:
            out.append(
                SugraInstitutionalOwnershipData(
                    symbol=symbol,
                    date=h.get("date_reported"),
                    holder=h.get("holder"),
                    shares=h.get("shares"),
                    value=h.get("value"),
                    pct_held=h.get("pct_held"),
                    pct_change=h.get("pct_change"),
                )
            )
        return out
