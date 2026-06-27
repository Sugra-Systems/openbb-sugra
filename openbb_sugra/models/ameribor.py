"""Sugra AMERIBOR Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.ameribor import (
    AmeriborData,
    AmeriborQueryParams,
)
from pydantic import Field

# AMERIBOR is published as one FRED series per tenor.
_MATURITY_TO_IDS = {
    "all": ["AMERIBOR", "AMBOR30", "AMBOR90", "AMBOR30T", "AMBOR90T"],
    "overnight": ["AMERIBOR"],
    "average_30d": ["AMBOR30"],
    "average_90d": ["AMBOR90"],
    "term_30d": ["AMBOR30T"],
    "term_90d": ["AMBOR90T"],
}
# The maturity label carried on each output row (the standard model requires it).
_ID_TO_MATURITY = {
    "AMERIBOR": "overnight",
    "AMBOR30": "day_30",
    "AMBOR90": "day_90",
    "AMBOR30T": "day_30",
    "AMBOR90T": "day_90",
}
_MATURITY_ORDER = {"overnight": 0, "day_30": 1, "day_90": 2}
_DEFAULT = "all"


class SugraAmeriborQueryParams(AmeriborQueryParams):
    """Sugra AMERIBOR Query Parameters."""

    maturity: Literal[
        "all", "overnight", "average_30d", "average_90d", "term_30d", "term_90d"
    ] = Field(default=_DEFAULT, description="Period of AMERIBOR rate.")


class SugraAmeriborData(AmeriborData):
    """Sugra AMERIBOR Data."""


class SugraAmeriborFetcher(Fetcher[SugraAmeriborQueryParams, list[SugraAmeriborData]]):
    """Fetch AMERIBOR overnight and term rates (AMBOR* series) from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraAmeriborQueryParams:
        """Transform the query parameters."""
        return SugraAmeriborQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraAmeriborQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw AMERIBOR series (one per selected tenor) from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        ids = _MATURITY_TO_IDS[query.maturity or _DEFAULT]
        return await fred_series_payloads(
            api_key, ids, start_date=query.start_date, end_date=query.end_date
        )

    @staticmethod
    def transform_data(
        query: SugraAmeriborQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraAmeriborData]:
        """Melt the per-tenor series into long rows. The rate is a fraction (value / 100)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows: list[dict] = []
        for series_id, payload in (data or {}).items():
            maturity = _ID_TO_MATURITY.get(series_id, series_id)
            title = payload.get("title") if isinstance(payload, dict) else None
            for obs in fred_observations(payload):
                rows.append(
                    {
                        "date": obs["date"],
                        "symbol": series_id,
                        "rate": obs["value"] / 100,
                        "maturity": maturity,
                        "title": title,
                    }
                )
        if not rows:
            raise EmptyDataError("No AMERIBOR observations returned.")
        rows.sort(key=lambda r: (r["date"], _MATURITY_ORDER.get(r["maturity"], 99)))
        return [SugraAmeriborData.model_validate(r) for r in rows]
