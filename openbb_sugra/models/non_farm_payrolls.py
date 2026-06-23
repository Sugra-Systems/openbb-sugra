"""Sugra Non-Farm Payrolls Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.non_farm_payrolls import (
    NonFarmPayrollsData,
    NonFarmPayrollsQueryParams,
)

_SERIES_ID = "PAYEMS"


class SugraNonFarmPayrollsQueryParams(NonFarmPayrollsQueryParams):
    """Sugra Non-Farm Payrolls Query Parameters."""


class SugraNonFarmPayrollsData(NonFarmPayrollsData):
    """Sugra Non-Farm Payrolls Data."""


class SugraNonFarmPayrollsFetcher(
    Fetcher[SugraNonFarmPayrollsQueryParams, list[SugraNonFarmPayrollsData]]
):
    """Fetch Non-Farm Payrolls (PAYEMS) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraNonFarmPayrollsQueryParams:
        """Transform the query parameters."""
        return SugraNonFarmPayrollsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraNonFarmPayrollsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw PAYEMS series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v1/fred/series/{_SERIES_ID}", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraNonFarmPayrollsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraNonFarmPayrollsData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        observations = (data or {}).get("observations") or []
        if not observations:
            raise EmptyDataError("No Non-Farm Payrolls observations returned.")
        rows: list[SugraNonFarmPayrollsData] = []
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
                SugraNonFarmPayrollsData.model_validate(
                    {"date": obs["date"], "symbol": _SERIES_ID, "value": value}
                )
            )
        if not rows:
            raise EmptyDataError("No Non-Farm Payrolls observations matched the query.")
        return rows
