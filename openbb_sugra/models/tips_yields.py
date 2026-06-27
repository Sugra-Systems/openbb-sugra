"""Sugra TIPS Yields Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.tips_yields import (
    TipsYieldsData,
    TipsYieldsQueryParams,
)
from pydantic import Field


class SugraTipsYieldsQueryParams(TipsYieldsQueryParams):
    """Sugra TIPS Yields Query Parameters (mirrors the fred provider extras)."""

    maturity: Literal["5", "10", "20", "30"] | None = Field(
        default=None,
        description="The tenor of the security in years (5/10/20/30); defaults to all.",
        json_schema_extra={"choices": ["5", "10", "20", "30"]},
    )
    frequency: (
        Literal[
            "a", "q", "m", "w", "d", "wef", "weth", "wew", "wetu", "wem",
            "wesu", "wesa", "bwew", "bwem",
        ]
        | None
    ) = Field(default=None, description="Frequency aggregation of the observations.")
    aggregation_method: Literal["avg", "sum", "eop"] | None = Field(
        default=None, description="Aggregation method when frequency is set."
    )
    transform: (
        Literal["chg", "ch1", "pch", "pc1", "pca", "cch", "cca"] | None
    ) = Field(default=None, description="The value transformation.")


class SugraTipsYieldsData(TipsYieldsData):
    """Sugra TIPS Yields Data."""


class SugraTipsYieldsFetcher(
    Fetcher[SugraTipsYieldsQueryParams, list[SugraTipsYieldsData]]
):
    """Fetch TIPS real yields from the Sugra API.

    Backed by `/api/v1/fred/government/tips`, which resolves the live TIPS
    membership and does the per-security fan-out SERVER-SIDE (bounded + cached),
    so this fetcher makes ONE call. `value` is already a decimal fraction.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraTipsYieldsQueryParams:
        """Transform the query parameters."""
        return SugraTipsYieldsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraTipsYieldsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw TIPS payload from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.maturity:
            params["maturity"] = query.maturity
        if query.start_date:
            params["start_date"] = str(query.start_date)
        if query.end_date:
            params["end_date"] = str(query.end_date)
        if query.frequency:
            params["frequency"] = query.frequency
        if query.aggregation_method:
            params["aggregation_method"] = query.aggregation_method
        if query.transform:
            params["transform"] = query.transform
        response = await sugra_get("/api/v1/fred/government/tips", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraTipsYieldsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraTipsYieldsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        results = (data or {}).get("results") or []
        if not results:
            raise EmptyDataError("No TIPS yields data returned.")
        return [
            SugraTipsYieldsData.model_validate(r)
            for r in results
            if isinstance(r, dict) and r.get("date") is not None
        ]
