"""Sugra Index Constituents Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.index_constituents import (
    IndexConstituentsData,
    IndexConstituentsQueryParams,
)
from pydantic import Field

# Symbols that resolve to the S&P 500 constituents endpoint.
_SP500_ALIASES = {"^GSPC", "GSPC", "SPX", "^SPX", "SP500", "SPY", "^SP500"}


class SugraIndexConstituentsQueryParams(IndexConstituentsQueryParams):
    """Sugra Index Constituents Query Parameters."""


class SugraIndexConstituentsData(IndexConstituentsData):
    """Sugra Index Constituents Data."""

    sector: str | None = Field(
        default=None, alias="gics_sector", description="GICS sector of the constituent."
    )
    sub_industry: str | None = Field(
        default=None,
        alias="gics_sub_industry",
        description="GICS sub-industry of the constituent.",
    )
    date_added: str | None = Field(
        default=None, description="Date the constituent was added to the index."
    )
    cik: str | None = Field(default=None, description="Central Index Key (SEC) of the constituent.")


class SugraIndexConstituentsFetcher(
    Fetcher[SugraIndexConstituentsQueryParams, list[SugraIndexConstituentsData]]
):
    """Fetch index constituents from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraIndexConstituentsQueryParams:
        """Transform the query parameters."""
        return SugraIndexConstituentsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraIndexConstituentsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw constituents from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import OpenBBError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        symbol = (query.symbol or "").upper()
        if symbol not in _SP500_ALIASES:
            raise OpenBBError(
                f"Sugra only provides constituents for the S&P 500 "
                f"(use ^GSPC, SPX, or SP500); got '{query.symbol}'."
            )
        response = await sugra_get("/api/v1/equities/sp500/constituents", api_key)
        payload = envelope_data(response)
        rows = payload.get("constituents", []) if isinstance(payload, dict) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraIndexConstituentsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraIndexConstituentsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No index constituents returned.")
        rows = []
        for d in data:
            row = dict(d)
            row["symbol"] = d.get("ticker")
            rows.append(row)
        return [SugraIndexConstituentsData.model_validate(r) for r in rows]
