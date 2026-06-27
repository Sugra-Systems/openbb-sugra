"""Sugra Symbol Map Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.symbol_map import SymbolMapQueryParams
from openbb_core.provider.utils.descriptions import DATA_DESCRIPTIONS
from pydantic import Field


class SugraSymbolMapQueryParams(SymbolMapQueryParams):
    """Sugra Symbol Map Query Parameters.

    The ``query`` is a CIK (bare or zero-padded 10-digit).
    """


class SugraSymbolMapData(Data):
    """Sugra Symbol Map Data."""

    symbol: str = Field(description=DATA_DESCRIPTIONS.get("symbol", ""))


class SugraSymbolMapFetcher(Fetcher[SugraSymbolMapQueryParams, SugraSymbolMapData]):
    """Map a SEC EDGAR CIK to its ticker symbol via the Sugra API.

    Backed by the SEC EDGAR name-history endpoint, which carries the filer's
    current ticker symbols alongside its legal-name history.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraSymbolMapQueryParams:
        """Transform the query parameters."""
        return SugraSymbolMapQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraSymbolMapQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the EDGAR name-history record for the CIK from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        # This maps CIK -> symbol, so the query must be a CIK. Reject non-digit
        # input (e.g. a ticker) with a clear message instead of silently sending
        # it as a path segment. ASCII-gate the digit check so unicode "digits"
        # cannot build a nonsense path (house rule: isascii() + isdigit()).
        cik = (query.query or "").strip()
        if not (cik.isascii() and cik.isdigit()):
            raise OpenBBError(
                "Symbol map requires a CIK (digits only), e.g. '320193' or"
                f" '0000320193' - got {query.query!r}. To map a ticker -> CIK use"
                " cik_map."
            )
        # Canonicalise to the SEC 10-digit zero-padded form.
        cik = cik.zfill(10)

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v1/sec/edgar/{cik}/name-history", api_key)
        payload = envelope_data(response)
        if not isinstance(payload, dict) or not payload:
            raise EmptyDataError(f"No EDGAR record found for CIK '{query.query}'.")
        return payload

    @staticmethod
    def transform_data(
        query: SugraSymbolMapQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> SugraSymbolMapData:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        tickers = data.get("tickers") if isinstance(data, dict) else None
        symbol = tickers[0] if isinstance(tickers, list) and tickers else None
        if not symbol:
            raise EmptyDataError(f"No symbol found for CIK '{query.query}'.")
        return SugraSymbolMapData(symbol=str(symbol))
