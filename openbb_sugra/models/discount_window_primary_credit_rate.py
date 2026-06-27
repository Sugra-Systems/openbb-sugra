"""Sugra Discount Window Primary Credit Rate Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.dwpcr_rates import (
    DiscountWindowPrimaryCreditRateData,
    DiscountWindowPrimaryCreditRateParams,
)
from pydantic import Field

# Each frequency variant of the DWPCR is its own FRED series (mirrors the
# upstream FRED provider's parameter map).
_PARAMETER_TO_SERIES = {
    "daily_excl_weekend": "DPCREDIT",
    "monthly": "MPCREDIT",
    "weekly": "WPCREDIT",
    "daily": "RIFSRPF02ND",
    "annual": "RIFSRPF02NA",
}
_DEFAULT = "daily_excl_weekend"


class SugraDiscountWindowPrimaryCreditRateQueryParams(DiscountWindowPrimaryCreditRateParams):
    """Sugra Discount Window Primary Credit Rate Query Parameters."""

    parameter: Literal["daily_excl_weekend", "monthly", "weekly", "daily", "annual"] = Field(
        default=_DEFAULT,
        description="The frequency variant of the Discount Window Primary Credit Rate.",
    )


class SugraDiscountWindowPrimaryCreditRateData(DiscountWindowPrimaryCreditRateData):
    """Sugra Discount Window Primary Credit Rate Data."""


class SugraDiscountWindowPrimaryCreditRateFetcher(
    Fetcher[
        SugraDiscountWindowPrimaryCreditRateQueryParams,
        list[SugraDiscountWindowPrimaryCreditRateData],
    ]
):
    """Fetch the Discount Window Primary Credit Rate (DPCREDIT family) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraDiscountWindowPrimaryCreditRateQueryParams:
        """Transform the query parameters."""
        return SugraDiscountWindowPrimaryCreditRateQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraDiscountWindowPrimaryCreditRateQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw DWPCR series for the chosen frequency from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        series_id = _PARAMETER_TO_SERIES[query.parameter or _DEFAULT]
        params: dict[str, Any] = {"limit": 1000, "sort_order": "desc"}
        if query.start_date:
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        response = await sugra_get(f"/api/v1/fred/series/{series_id}", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraDiscountWindowPrimaryCreditRateQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraDiscountWindowPrimaryCreditRateData]:
        """Validate into the standard model (the rate is an as-is percent)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows = fred_observations(data)
        if not rows:
            raise EmptyDataError("No Discount Window Primary Credit Rate observations returned.")
        return [
            SugraDiscountWindowPrimaryCreditRateData.model_validate(
                {"date": r["date"], "rate": r["value"]}
            )
            for r in rows
        ]
