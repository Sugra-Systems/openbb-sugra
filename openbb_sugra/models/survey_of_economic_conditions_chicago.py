"""Sugra Survey of Economic Conditions - Chicago Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.survey_of_economic_conditions_chicago import (
    SurveyOfEconomicConditionsChicagoData,
    SurveyOfEconomicConditionsChicagoQueryParams,
)

# One FRED series per field (Chicago Fed Survey of Business Conditions, CFSBC*).
# Series ids ported clean-room from the openbb_fred blueprint (openbb_fred is not
# a dependency). Every series is a diffusion index, so all values are AS-IS (no
# x-frontend_multiply on any standard-model field -> no /100). Unlike openbb_fred
# - which surfaces four columns under FRED-style names (capital_spending_expectations
# / current_hiring_index / labor_costs_index / non_labor_costs_index) and leaves the
# matching standard SurveyOfEconomicConditionsChicagoData fields empty - we map to
# the standard field names so the declared model fields actually populate.
_ID_TO_FIELD = {
    "CFSBCACTIVITY": "activity_index",
    "CFSBCOUTLOOK": "one_year_outlook",
    "CFSBCACTIVITYMFG": "manufacturing_activity",
    "CFSBCACTIVITYNMFG": "non_manufacturing_activity",
    "CFSBCCAPXEXP": "capital_expenditures_expectations",
    "CFSBCHIRINGEXP": "hiring_expectations",
    "CFSBCHIRING": "current_hiring",
    "CFSBCLABORCOSTS": "labor_costs",
    "CFSBCNONLABORCOSTS": "non_labor_costs",
}


class SugraSurveyOfEconomicConditionsChicagoQueryParams(
    SurveyOfEconomicConditionsChicagoQueryParams
):
    """Sugra Survey of Economic Conditions - Chicago Query Parameters."""


class SugraSurveyOfEconomicConditionsChicagoData(
    SurveyOfEconomicConditionsChicagoData
):
    """Sugra Survey of Economic Conditions - Chicago Data."""


class SugraSurveyOfEconomicConditionsChicagoFetcher(
    Fetcher[
        SugraSurveyOfEconomicConditionsChicagoQueryParams,
        list[SugraSurveyOfEconomicConditionsChicagoData],
    ]
):
    """Fetch the Chicago Fed Survey of Business Conditions (CFSBC*) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraSurveyOfEconomicConditionsChicagoQueryParams:
        """Transform the query parameters."""
        return SugraSurveyOfEconomicConditionsChicagoQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraSurveyOfEconomicConditionsChicagoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the nine Chicago Fed survey series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        return await fred_series_payloads(
            api_key,
            list(_ID_TO_FIELD),
            start_date=query.start_date,
            end_date=query.end_date,
        )

    @staticmethod
    def transform_data(
        query: SugraSurveyOfEconomicConditionsChicagoQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraSurveyOfEconomicConditionsChicagoData]:
        """Pivot the nine series per date. All fields are diffusion indices -> AS-IS."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        by_date: dict[str, dict] = {}
        for series_id, payload in (data or {}).items():
            field = _ID_TO_FIELD.get(series_id)
            if field is None:
                continue
            for obs in fred_observations(payload):
                # Diffusion index - no x-frontend_multiply, so store the raw value.
                by_date.setdefault(obs["date"], {})[field] = obs["value"]

        rows = [{"date": date, **by_date[date]} for date in sorted(by_date)]
        if not rows:
            raise EmptyDataError(
                "No Chicago Fed Survey of Business Conditions observations returned."
            )
        return [
            SugraSurveyOfEconomicConditionsChicagoData.model_validate(r) for r in rows
        ]
