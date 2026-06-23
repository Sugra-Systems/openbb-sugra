"""Sugra Commitment of Traders (COT) Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.cot import (
    COTData,
    COTQueryParams,
)
from pydantic import Field


def _parse_date(value: Any) -> dateType | None:
    """Parse an ISO date or YYYYMMDD value into a date."""
    if value is None:
        return None
    text = str(value).strip()
    if len(text) == 8 and text.isascii() and text.isdigit():
        try:
            return dateType(int(text[:4]), int(text[4:6]), int(text[6:8]))
        except (ValueError, TypeError):
            return None
    # pylint: disable=import-outside-toplevel
    try:
        from dateutil import parser

        return parser.parse(text).date()
    except (ValueError, TypeError, ImportError):
        return None


class SugraCOTQueryParams(COTQueryParams):
    """Sugra COT Query Parameters."""

    limit: int | None = Field(
        default=None, description="Maximum number of weekly reports to return."
    )


class SugraCOTData(COTData):
    """Sugra COT Data."""

    contract_market_name: str | None = Field(default=None, description="Contract market name.")
    contract_code: str | None = Field(default=None, description="CFTC contract code.")
    open_interest_all: int | None = Field(default=None, description="Open interest, all contracts.")
    noncomm_positions_long_all: int | None = Field(
        default=None, description="Non-commercial long positions, all."
    )
    noncomm_positions_short_all: int | None = Field(
        default=None, description="Non-commercial short positions, all."
    )
    comm_positions_long_all: int | None = Field(
        default=None, description="Commercial long positions, all."
    )
    comm_positions_short_all: int | None = Field(
        default=None, description="Commercial short positions, all."
    )


class SugraCOTFetcher(Fetcher[SugraCOTQueryParams, list[SugraCOTData]]):
    """Fetch Commitment of Traders legacy reports from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCOTQueryParams:
        """Transform the query parameters."""
        return SugraCOTQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCOTQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw COT records from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {"market": query.code}
        if query.limit:
            params["limit"] = query.limit
        response = await sugra_get("/api/v1/cot/legacy", api_key, params)
        payload = envelope_data(response)
        rows = payload.get("records", []) if isinstance(payload, dict) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraCOTQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraCOTData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No COT records returned for the market.")

        start = query.start_date
        end = query.end_date
        results: list[SugraCOTData] = []
        for item in data:
            parsed = _parse_date(item.get("report_date"))
            if parsed is None:
                continue
            if start and parsed < start:
                continue
            if end and parsed > end:
                continue
            results.append(
                SugraCOTData(
                    date=parsed,
                    market_and_exchange_names=item.get("market_and_exchange_names"),
                    contract_market_name=item.get("contract_market_name"),
                    contract_code=item.get("contract_code"),
                    open_interest_all=item.get("open_interest_all"),
                    noncomm_positions_long_all=item.get("noncomm_positions_long_all"),
                    noncomm_positions_short_all=item.get("noncomm_positions_short_all"),
                    comm_positions_long_all=item.get("comm_positions_long_all"),
                    comm_positions_short_all=item.get("comm_positions_short_all"),
                )
            )

        if not results:
            raise EmptyDataError("No COT rows produced for the market.")
        return results
