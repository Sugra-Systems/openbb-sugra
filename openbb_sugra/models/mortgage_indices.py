"""Sugra Mortgage Indices Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.mortgage_indices import (
    MortgageIndicesData,
    MortgageIndicesQueryParams,
)
from pydantic import Field

# Optimal Blue Mortgage Market Indices (OBMMI*) are published as one FRED series
# per index. Catalog ported clean-room from the openbb_fred blueprint.
MORTGAGE_ID_TO_TITLE = {
    "OBMMIC30YF": "30-Year Fixed Rate Conforming",
    "OBMMIC30YFNA": "30-Year Fixed Rate Conforming Non-Adjusted",
    "OBMMIJUMBO30YF": "30-Year Fixed Rate Jumbo",
    "OBMMIFHA30YF": "30-Year Fixed Rate FHA",
    "OBMMIVA30YF": "30-Year Fixed Rate Veterans Affairs",
    "OBMMIUSDA30YF": "30-Year Fixed Rate USDA",
    "OBMMIC15YF": "15-Year Fixed Rate Conforming",
    "OBMMIC30YFLVLE80FGE740": "30-Year Fixed Rate Conforming LTV <= 80 FICO >= 740",
    "OBMMIC30YFLVLE80FB720A739": "30-Year Fixed Rate Conforming LTV <= 80 FICO 720-739",
    "OBMMIC30YFLVLE80FB700A719": "30-Year Fixed Rate Conforming LTV <= 80 FICO 700-719",
    "OBMMIC30YFLVLE80FB680A699": "30-Year Fixed Rate Conforming LTV <= 80 FICO 680-699",
    "OBMMIC30YFLVLE80FLT680": "30-Year Fixed Rate Conforming LTV <= 80 FICO < 680",
    "OBMMIC30YFLVGT80FGE740": "30-Year Fixed Rate Conforming LTV > 80 FICO >= 740",
    "OBMMIC30YFLVGT80FB720A739": "30-Year Fixed Rate Conforming LTV > 80 FICO 720-739",
    "OBMMIC30YFLVGT80FB700A719": "30-Year Fixed Rate Conforming LTV > 80 FICO 700-719",
    "OBMMIC30YFLVGT80FB680A699": "30-Year Fixed Rate Conforming LTV > 80 FICO 680-699",
    "OBMMIC30YFLVGT80FLT680": "30-Year Fixed Rate Conforming LTV > 80 FICO < 680",
}

MORTGAGE_GROUPS = {
    "primary": [
        "OBMMIC30YF",
        "OBMMIC30YFNA",
        "OBMMIJUMBO30YF",
        "OBMMIFHA30YF",
        "OBMMIVA30YF",
        "OBMMIUSDA30YF",
        "OBMMIC15YF",
    ],
    "ltv_lte_80": [
        "OBMMIC30YFLVLE80FGE740",
        "OBMMIC30YFLVLE80FB720A739",
        "OBMMIC30YFLVLE80FB700A719",
        "OBMMIC30YFLVLE80FB680A699",
        "OBMMIC30YFLVLE80FLT680",
    ],
    "ltv_gt_80": [
        "OBMMIC30YFLVGT80FGE740",
        "OBMMIC30YFLVGT80FB720A739",
        "OBMMIC30YFLVGT80FB700A719",
        "OBMMIC30YFLVGT80FB680A699",
        "OBMMIC30YFLVGT80FLT680",
    ],
}

MORTGAGE_CHOICES_TO_ID = {
    "primary": ",".join(MORTGAGE_GROUPS["primary"]),
    "ltv_lte_80": ",".join(MORTGAGE_GROUPS["ltv_lte_80"]),
    "ltv_gt_80": ",".join(MORTGAGE_GROUPS["ltv_gt_80"]),
    "conforming_30y": "OBMMIC30YF",
    "conforming_30y_na": "OBMMIC30YFNA",
    "jumbo_30y": "OBMMIJUMBO30YF",
    "fha_30y": "OBMMIFHA30YF",
    "va_30y": "OBMMIVA30YF",
    "usda_30y": "OBMMIUSDA30YF",
    "conforming_15y": "OBMMIC15YF",
    "ltv_lte80_fico_ge740": "OBMMIC30YFLVLE80FGE740",
    "ltv_lte80_fico_a720b739": "OBMMIC30YFLVLE80FB720A739",
    "ltv_lte80_fico_a700b719": "OBMMIC30YFLVLE80FB700A719",
    "ltv_lte80_fico_a680b699": "OBMMIC30YFLVLE80FB680A699",
    "ltv_lte80_fico_lt680": "OBMMIC30YFLVLE80FLT680",
    "ltv_gt80_fico_ge740": "OBMMIC30YFLVGT80FGE740",
    "ltv_gt80_fico_a720b739": "OBMMIC30YFLVGT80FB720A739",
    "ltv_gt80_fico_a700b719": "OBMMIC30YFLVGT80FB700A719",
    "ltv_gt80_fico_a680b699": "OBMMIC30YFLVGT80FB680A699",
    "ltv_gt80_fico_lt680": "OBMMIC30YFLVGT80FLT680",
}

MortgageChoices = Literal[
    "primary",
    "ltv_lte_80",
    "ltv_gt_80",
    "conforming_30y",
    "conforming_30y_na",
    "jumbo_30y",
    "fha_30y",
    "va_30y",
    "usda_30y",
    "conforming_15y",
    "ltv_lte80_fico_ge740",
    "ltv_lte80_fico_a720b739",
    "ltv_lte80_fico_a700b719",
    "ltv_lte80_fico_a680b699",
    "ltv_lte80_fico_lt680",
    "ltv_gt80_fico_ge740",
    "ltv_gt80_fico_a720b739",
    "ltv_gt80_fico_a700b719",
    "ltv_gt80_fico_a680b699",
    "ltv_gt80_fico_lt680",
]

# Stable presentation order for the symbol -> name melt (catalog key order).
_ID_ORDER = {series_id: i for i, series_id in enumerate(MORTGAGE_ID_TO_TITLE)}
_DEFAULT = "primary"


def _resolve_ids(index: str | None) -> list[str]:
    """Expand a comma-separated ``index`` selection into ordered, unique ids."""
    choices = [c.strip() for c in (index or _DEFAULT).split(",") if c.strip()]
    ids: list[str] = []
    for choice in choices:
        mapped = MORTGAGE_CHOICES_TO_ID.get(choice)
        if not mapped:
            continue
        for series_id in mapped.split(","):
            if series_id not in ids:
                ids.append(series_id)
    if not ids:
        ids = MORTGAGE_CHOICES_TO_ID[_DEFAULT].split(",")
    return ids


class SugraMortgageIndicesQueryParams(MortgageIndicesQueryParams):
    """Sugra Mortgage Indices Query Parameters."""

    __json_schema_extra__ = {
        "index": {
            "multiple_items_allowed": True,
            "choices": list(MORTGAGE_CHOICES_TO_ID),
        }
    }

    index: MortgageChoices | str = Field(
        default=_DEFAULT,
        description="The specific index, or index group, to query. Default is"
        " the 'primary' group.",
    )


class SugraMortgageIndicesData(MortgageIndicesData):
    """Sugra Mortgage Indices Data."""


class SugraMortgageIndicesFetcher(
    Fetcher[SugraMortgageIndicesQueryParams, list[SugraMortgageIndicesData]]
):
    """Fetch Optimal Blue Mortgage Market Indices (OBMMI*) from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraMortgageIndicesQueryParams:
        """Transform the query parameters."""
        return SugraMortgageIndicesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraMortgageIndicesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the selected OBMMI mortgage index series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        ids = _resolve_ids(query.index)
        return await fred_series_payloads(
            api_key, ids, start_date=query.start_date, end_date=query.end_date
        )

    @staticmethod
    def transform_data(
        query: SugraMortgageIndicesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraMortgageIndicesData]:
        """Melt the per-index series into long rows. The rate is a fraction (value / 100)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows: list[dict] = []
        for series_id, payload in (data or {}).items():
            name = MORTGAGE_ID_TO_TITLE.get(series_id)
            for obs in fred_observations(payload):
                rows.append(
                    {
                        "date": obs["date"],
                        "symbol": series_id,
                        # rate carries x-frontend_multiply:100 -> store the fraction.
                        "rate": obs["value"] / 100,
                        "name": name,
                    }
                )
        if not rows:
            raise EmptyDataError("No mortgage index observations returned.")
        rows.sort(key=lambda r: (r["date"], _ID_ORDER.get(r["symbol"], 99)))
        return [SugraMortgageIndicesData.model_validate(r) for r in rows]
