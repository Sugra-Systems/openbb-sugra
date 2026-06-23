"""Sugra Personal Consumption Expenditures Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.personal_consumption_expenditures import (
    PersonalConsumptionExpendituresData,
    PersonalConsumptionExpendituresQueryParams,
)

_SERIES_ID = "PCE"


class SugraPersonalConsumptionExpendituresQueryParams(PersonalConsumptionExpendituresQueryParams):
    """Sugra Personal Consumption Expenditures Query Parameters."""


class SugraPersonalConsumptionExpendituresData(PersonalConsumptionExpendituresData):
    """Sugra Personal Consumption Expenditures Data."""


class SugraPersonalConsumptionExpendituresFetcher(
    Fetcher[
        SugraPersonalConsumptionExpendituresQueryParams,
        list[SugraPersonalConsumptionExpendituresData],
    ]
):
    """Fetch Personal Consumption Expenditures (PCE) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraPersonalConsumptionExpendituresQueryParams:
        """Transform the query parameters."""
        return SugraPersonalConsumptionExpendituresQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraPersonalConsumptionExpendituresQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw PCE series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get(f"/api/v1/fred/series/{_SERIES_ID}", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: SugraPersonalConsumptionExpendituresQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraPersonalConsumptionExpendituresData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        observations = (data or {}).get("observations") or []
        if not observations:
            raise EmptyDataError("No PCE observations returned.")
        rows: list[SugraPersonalConsumptionExpendituresData] = []
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
                SugraPersonalConsumptionExpendituresData.model_validate(
                    {"date": obs["date"], "symbol": _SERIES_ID, "value": value}
                )
            )
        if not rows:
            raise EmptyDataError("No PCE observations matched the query.")
        return rows
