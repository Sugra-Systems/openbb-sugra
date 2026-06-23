"""Sugra Form 13F-HR Model."""

# pylint: disable=unused-argument

from datetime import date as dateType
from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.form_13FHR import (
    Form13FHRData,
    Form13FHRQueryParams,
)


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


def _to_int(value: Any) -> int | None:
    """Coerce a value to int, returning None on failure."""
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (ValueError, TypeError):
        return None


class SugraForm13FHRQueryParams(Form13FHRQueryParams):
    """Sugra Form 13F-HR Query Parameters."""


class SugraForm13FHRData(Form13FHRData):
    """Sugra Form 13F-HR Data."""


class SugraForm13FHRFetcher(Fetcher[SugraForm13FHRQueryParams, list[SugraForm13FHRData]]):
    """Fetch SEC Form 13F-HR holdings from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraForm13FHRQueryParams:
        """Transform the query parameters."""
        return SugraForm13FHRQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraForm13FHRQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw 13F portfolio from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        cik = str(query.symbol).strip()
        response = await sugra_get(f"/api/v1/sec/13f/{cik}/holdings", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraForm13FHRQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraForm13FHRData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        positions = data.get("positions") if isinstance(data, dict) else None
        if not positions:
            raise EmptyDataError("No 13F holdings returned for the filer.")

        period_ending = _parse_date(data.get("period_of_report"))
        if period_ending is None:
            raise EmptyDataError("13F filing is missing a period_of_report date.")

        results: list[SugraForm13FHRData] = []
        for pos in positions:
            if not isinstance(pos, dict):
                continue
            issuer = pos.get("issuer")
            cusip = pos.get("cusip")
            asset_class = pos.get("title")
            value = _to_int(pos.get("value_usd_thousands"))
            principal = _to_int(pos.get("shares"))
            if not issuer or not cusip or not asset_class or value is None or principal is None:
                continue
            results.append(
                SugraForm13FHRData(
                    period_ending=period_ending,
                    issuer=str(issuer),
                    cusip=str(cusip),
                    asset_class=str(asset_class),
                    value=value * 1000,
                    principal_amount=principal,
                    security_type=pos.get("shares_type"),
                    option_type=pos.get("put_call"),
                    investment_discretion=pos.get("investment_discretion"),
                    voting_authority_sole=_to_int(pos.get("voting_sole")),
                    voting_authority_shared=_to_int(pos.get("voting_shared")),
                    voting_authority_none=_to_int(pos.get("voting_none")),
                )
            )

        if not results:
            raise EmptyDataError("No complete 13F holding rows produced.")
        return results
