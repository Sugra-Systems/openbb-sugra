"""Sugra Federal Funds Rate Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.federal_funds_rate import (
    FederalFundsRateData,
    FederalFundsRateQueryParams,
)


class SugraFederalFundsRateQueryParams(FederalFundsRateQueryParams):
    """Sugra Federal Funds Rate Query Parameters."""


class SugraFederalFundsRateData(FederalFundsRateData):
    """Sugra Federal Funds Rate Data."""


class SugraFederalFundsRateFetcher(
    Fetcher[SugraFederalFundsRateQueryParams, list[SugraFederalFundsRateData]]
):
    """Fetch the effective Federal Funds Rate (DFF) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraFederalFundsRateQueryParams:
        """Transform the query parameters."""
        return SugraFederalFundsRateQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraFederalFundsRateQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw DFF series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        response = await sugra_get("/api/v1/fred/series/DFF", api_key, params)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraFederalFundsRateQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraFederalFundsRateData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        observations = (data or {}).get("observations") or []
        if not observations:
            raise EmptyDataError("No Federal Funds Rate observations returned.")
        rows: list[SugraFederalFundsRateData] = []
        for obs in observations:
            if not isinstance(obs, dict) or obs.get("date") is None:
                continue
            value = obs.get("value")
            if isinstance(value, str):
                if value.strip() in {"", "."}:
                    continue
                value = float(value)
            if value is None:
                continue
            rows.append(
                SugraFederalFundsRateData.model_validate({"date": obs["date"], "rate": value})
            )
        if not rows:
            raise EmptyDataError("No Federal Funds Rate observations matched the query.")
        return rows
