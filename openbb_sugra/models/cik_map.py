"""Sugra CIK Map Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.cik_map import (
    CikMapData,
    CikMapQueryParams,
)


class SugraCikMapQueryParams(CikMapQueryParams):
    """Sugra CIK Map Query Parameters."""


class SugraCikMapData(CikMapData):
    """Sugra CIK Map Data."""


class SugraCikMapFetcher(Fetcher[SugraCikMapQueryParams, SugraCikMapData]):
    """Map a ticker symbol to its SEC EDGAR CIK via the Sugra API.

    Backed by the SEC EDGAR name-history endpoint, which carries the zero-padded
    10-digit CIK alongside the filer's legal-name history.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCikMapQueryParams:
        """Transform the query parameters."""
        return SugraCikMapQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCikMapQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the EDGAR name-history record for the symbol from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(
            f"/api/v1/sec/edgar/{query.symbol}/name-history", api_key
        )
        payload = envelope_data(response)
        if not isinstance(payload, dict) or not payload:
            raise EmptyDataError(f"No CIK found for symbol '{query.symbol}'.")
        return payload

    @staticmethod
    def transform_data(
        query: SugraCikMapQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> SugraCikMapData:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        cik = data.get("cik") if isinstance(data, dict) else None
        if cik is None:
            raise EmptyDataError(f"No CIK found for symbol '{query.symbol}'.")
        # The upstream already returns a 10-digit zero-padded CIK; enforce the
        # invariant at our boundary so a bare CIK still complies with the
        # standard model rather than trusting upstream formatting.
        return SugraCikMapData(cik=str(cik).zfill(10))
