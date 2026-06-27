"""Sugra Senior Loan Officer Opinion Survey Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.senior_loan_officer_survey import (
    SeniorLoanOfficerSurveyData,
    SeniorLoanOfficerSurveyQueryParams,
)
from pydantic import Field

# Each SLOOS category maps to a comma-joined set of DR*/SUBLP* / STDS* / DEM*
# FRED series ids (net-percent-of-banks figures). Ported clean-room VERBATIM
# from the openbb_fred blueprint (openbb_fred is not a dependency, so the
# catalog lives here). The selected category's ids are fetched and melted into
# long rows; the default category ("spreads") is three series, so a no-arg call
# is selector-bounded - it never fans out to the full SLOOS universe.
SLOOS_CATEGORIES = {
    "spreads": "DRISCFLM,DRISCFS,SUBLPDCLCTSNQ",
    "consumer": "DRIWCIL,STDSOTHCONS,SUBLPDCLHSNQ",
    "auto": "DEMAUTO,STDSAUTO",
    "credit_card": "DEMCC,DRTSCLCC,SUBLPDCLCTSNQ",
    "firms": "DRISCFLM,DRISCFS,DRTSCILM,DRTSCIS",
    "mortgage": "DRTSSP,SUBLPDHMSGNQ,SUBLPDHMSENQ,SUBLPDHMSJNQ,SUBLPDHMSQNQ,SUBLPDHMSMNQ",
    "commercial_real_estate": "SUBLPDRCSN,SUBLPDRCSM,SUBLPDRCDCLGNQ,SUBLPFRCSNQ",
    "standards": "DRTSCILM,DRTSCIS,DRTSCLCC,STDSAUTO,DRTSSP,SUBLPDHMSGNQ,STDSOTHCONS,SUBLPDHMSENQ,SUBLPDHMSJNQ,SUBLPDHMSQNQ,SUBLPDHMSMNQ,SUBLPDCLHSNQ,SUBLPDRCSN,SUBLPDRCSM,SUBLPFRCSNQ,SUBLPFCISNQ,SUBLPDMBSXWBNQ",  # noqa: E501
    "demand": "DEMCC,DEMAUTO,SUBLPDMODXWBNQ,SUBLPDMBDXWBNQ,SUBLPDRCDCLGNQ",
    "foreign_banks": "SUBLPFRCSNQ,SUBLPFCISNQ",
}
_DEFAULT_CATEGORY = "spreads"


class SugraSeniorLoanOfficerSurveyQueryParams(SeniorLoanOfficerSurveyQueryParams):
    """Sugra Senior Loan Officer Opinion Survey Query Parameters."""

    category: Literal[
        "spreads",
        "consumer",
        "auto",
        "credit_card",
        "firms",
        "mortgage",
        "commercial_real_estate",
        "standards",
        "demand",
        "foreign_banks",
    ] = Field(
        default=_DEFAULT_CATEGORY,
        description="Category of survey response.",
        json_schema_extra={"choices": list(SLOOS_CATEGORIES.keys())},
    )


class SugraSeniorLoanOfficerSurveyData(SeniorLoanOfficerSurveyData):
    """Sugra Senior Loan Officer Opinion Survey Data."""


class SugraSeniorLoanOfficerSurveyFetcher(
    Fetcher[
        SugraSeniorLoanOfficerSurveyQueryParams,
        list[SugraSeniorLoanOfficerSurveyData],
    ]
):
    """Fetch Senior Loan Officer Opinion Survey series (DR*/SUBLP*) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraSeniorLoanOfficerSurveyQueryParams:
        """Transform the query parameters."""
        return SugraSeniorLoanOfficerSurveyQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraSeniorLoanOfficerSurveyQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the selected category's SLOOS series (one per id) from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        ids = SLOOS_CATEGORIES[query.category or _DEFAULT_CATEGORY].split(",")
        return await fred_series_payloads(
            api_key, ids, start_date=query.start_date, end_date=query.end_date
        )

    @staticmethod
    def transform_data(
        query: SugraSeniorLoanOfficerSurveyQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraSeniorLoanOfficerSurveyData]:
        """Melt the per-series payloads into long rows.

        ``value`` is a net-percent-of-banks figure: the FRED blueprint stores it
        as a fraction (value / 100). The standard model ``value`` field carries
        no ``x-frontend_multiply`` override, so dividing by 100 is the explicit
        normalisation here. ``symbol`` and ``title`` are passthrough labels.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows: list[dict] = []
        for series_id, payload in (data or {}).items():
            title = payload.get("title") if isinstance(payload, dict) else None
            for obs in fred_observations(payload):
                rows.append(
                    {
                        "date": obs["date"],
                        "symbol": series_id,
                        # net-percent-of-banks -> store the fraction (value / 100).
                        "value": obs["value"] / 100,
                        "title": title,
                    }
                )
        if not rows:
            raise EmptyDataError("No senior loan officer survey observations returned.")
        rows.sort(key=lambda r: (r["date"], r["symbol"]))
        return [SugraSeniorLoanOfficerSurveyData.model_validate(r) for r in rows]
