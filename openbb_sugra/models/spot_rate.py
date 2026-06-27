"""Sugra Spot Rate Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.spot import (
    SpotRateData,
    SpotRateQueryParams,
)

# HQM Corporate Bond spot-rate / par-yield FRED series, keyed by
# (maturity_in_years, category). Ported verbatim (clean-room) from the upstream
# FRED provider's corporate_spot_rates.csv. The maturity is the float parsed
# from the CSV "Maturity" column (the odd "6 y" 6-month row keeps maturity 6.0,
# so a maturity of 6.0 spot_rate matches both HQMCB6MT and HQMCB6YR, exactly as
# the source CSV does). openbb_fred is NOT a dependency, so these are inlined.
_CATALOG: tuple[tuple[float, str, str], ...] = (
    (1, "spot_rate", "HQMCB1YR"),
    (1.5, "spot_rate", "HQMCB1Y6M"),
    (2, "par_yield", "HQMCB2YRP"),
    (2, "spot_rate", "HQMCB2YR"),
    (2.5, "spot_rate", "HQMCB2Y6M"),
    (3, "spot_rate", "HQMCB3YR"),
    (3.5, "spot_rate", "HQMCB3Y6M"),
    (4, "spot_rate", "HQMCB4YR"),
    (4.5, "spot_rate", "HQMCB4Y6M"),
    (5, "par_yield", "HQMCB5YRP"),
    (5, "spot_rate", "HQMCB5YR"),
    (5.5, "spot_rate", "HQMCB5Y6M"),
    (6, "spot_rate", "HQMCB6MT"),
    (6, "spot_rate", "HQMCB6YR"),
    (6.5, "spot_rate", "HQMCB6Y6M"),
    (7, "spot_rate", "HQMCB7YR"),
    (7.5, "spot_rate", "HQMCB7Y6M"),
    (8, "spot_rate", "HQMCB8YR"),
    (8.5, "spot_rate", "HQMCB8Y6M"),
    (9, "spot_rate", "HQMCB9YR"),
    (9.5, "spot_rate", "HQMCB9Y6M"),
    (10, "par_yield", "HQMCB10YRP"),
    (10, "spot_rate", "HQMCB10YR"),
    (10.5, "spot_rate", "HQMCB10Y6M"),
    (11, "spot_rate", "HQMCB11YR"),
    (11.5, "spot_rate", "HQMCB11Y6M"),
    (12, "spot_rate", "HQMCB12YR"),
    (12.5, "spot_rate", "HQMCB12Y6M"),
    (13, "spot_rate", "HQMCB13YR"),
    (13.5, "spot_rate", "HQMCB13Y6M"),
    (14, "spot_rate", "HQMCB14YR"),
    (14.5, "spot_rate", "HQMCB14Y6M"),
    (15, "spot_rate", "HQMCB15YR"),
    (15.5, "spot_rate", "HQMCB15Y6M"),
    (16, "spot_rate", "HQMCB16YR"),
    (16.5, "spot_rate", "HQMCB16Y6M"),
    (17, "spot_rate", "HQMCB17YR"),
    (17.5, "spot_rate", "HQMCB17Y6M"),
    (18, "spot_rate", "HQMCB18YR"),
    (18.5, "spot_rate", "HQMCB18Y6M"),
    (19, "spot_rate", "HQMCB19YR"),
    (19.5, "spot_rate", "HQMCB19Y6M"),
    (20, "spot_rate", "HQMCB20YR"),
    (20.5, "spot_rate", "HQMCB20Y6M"),
    (21, "spot_rate", "HQMCB21YR"),
    (21.5, "spot_rate", "HQMCB21Y6M"),
    (22, "spot_rate", "HQMCB22YR"),
    (22.5, "spot_rate", "HQMCB22Y6M"),
    (23, "spot_rate", "HQMCB23YR"),
    (23.5, "spot_rate", "HQMCB23Y6M"),
    (24, "spot_rate", "HQMCB24YR"),
    (24.5, "spot_rate", "HQMCB24Y6M"),
    (25, "spot_rate", "HQMCB25YR"),
    (25.5, "spot_rate", "HQMCB25Y6M"),
    (26, "spot_rate", "HQMCB26YR"),
    (26.5, "spot_rate", "HQMCB26Y6M"),
    (27, "spot_rate", "HQMCB27YR"),
    (27.5, "spot_rate", "HQMCB27Y6M"),
    (28, "spot_rate", "HQMCB28YR"),
    (28.5, "spot_rate", "HQMCB28Y6M"),
    (29, "spot_rate", "HQMCB29YR"),
    (29.5, "spot_rate", "HQMCB29Y6M"),
    (30, "par_yield", "HQMCB30YRP"),
    (30, "spot_rate", "HQMCB30YR"),
    (30.5, "spot_rate", "HQMCB30Y6M"),
    (31, "spot_rate", "HQMCB31YR"),
    (31.5, "spot_rate", "HQMCB31Y6M"),
    (32, "spot_rate", "HQMCB32YR"),
    (32.5, "spot_rate", "HQMCB32Y6M"),
    (33, "spot_rate", "HQMCB33YR"),
    (33.5, "spot_rate", "HQMCB33Y6M"),
    (34, "spot_rate", "HQMCB34YR"),
    (34.5, "spot_rate", "HQMCB34Y6M"),
    (35, "spot_rate", "HQMCB35YR"),
    (35.5, "spot_rate", "HQMCB35Y6M"),
    (36, "spot_rate", "HQMCB36YR"),
    (36.5, "spot_rate", "HQMCB36Y6M"),
    (37, "spot_rate", "HQMCB37YR"),
    (37.5, "spot_rate", "HQMCB37Y6M"),
    (38, "spot_rate", "HQMCB38YR"),
    (38.5, "spot_rate", "HQMCB38Y6M"),
    (39, "spot_rate", "HQMCB39YR"),
    (39.5, "spot_rate", "HQMCB39Y6M"),
    (40, "spot_rate", "HQMCB40YR"),
    (40.5, "spot_rate", "HQMCB40Y6M"),
    (41, "spot_rate", "HQMCB41YR"),
    (41.5, "spot_rate", "HQMCB41Y6M"),
    (42, "spot_rate", "HQMCB42YR"),
    (42.5, "spot_rate", "HQMCB42Y6M"),
    (43, "spot_rate", "HQMCB43YR"),
    (43.5, "spot_rate", "HQMCB43Y6M"),
    (44, "spot_rate", "HQMCB44YR"),
    (44.5, "spot_rate", "HQMCB44Y6M"),
    (45, "spot_rate", "HQMCB45YR"),
    (45.5, "spot_rate", "HQMCB45Y6M"),
    (46, "spot_rate", "HQMCB46YR"),
    (46.5, "spot_rate", "HQMCB46Y6M"),
    (47, "spot_rate", "HQMCB47YR"),
    (47.5, "spot_rate", "HQMCB47Y6M"),
    (48, "spot_rate", "HQMCB48YR"),
    (48.5, "spot_rate", "HQMCB48Y6M"),
    (49, "spot_rate", "HQMCB49YR"),
    (49.5, "spot_rate", "HQMCB49Y6M"),
    (50, "spot_rate", "HQMCB50YR"),
    (50.5, "spot_rate", "HQMCB50Y6M"),
    (51, "spot_rate", "HQMCB51YR"),
    (51.5, "spot_rate", "HQMCB51Y6M"),
    (52, "spot_rate", "HQMCB52YR"),
    (52.5, "spot_rate", "HQMCB52Y6M"),
    (53, "spot_rate", "HQMCB53YR"),
    (53.5, "spot_rate", "HQMCB53Y6M"),
    (54, "spot_rate", "HQMCB54YR"),
    (54.5, "spot_rate", "HQMCB54Y6M"),
    (55, "spot_rate", "HQMCB55YR"),
    (55.5, "spot_rate", "HQMCB55Y6M"),
    (56, "spot_rate", "HQMCB56YR"),
    (56.5, "spot_rate", "HQMCB56Y6M"),
    (57, "spot_rate", "HQMCB57YR"),
    (57.5, "spot_rate", "HQMCB57Y6M"),
    (58, "spot_rate", "HQMCB58YR"),
    (58.5, "spot_rate", "HQMCB58Y6M"),
    (59, "spot_rate", "HQMCB59YR"),
    (59.5, "spot_rate", "HQMCB59Y6M"),
    (60, "spot_rate", "HQMCB60YR"),
    (60.5, "spot_rate", "HQMCB60Y6M"),
    (61, "spot_rate", "HQMCB61YR"),
    (61.5, "spot_rate", "HQMCB61Y6M"),
    (62, "spot_rate", "HQMCB62YR"),
    (62.5, "spot_rate", "HQMCB62Y6M"),
    (63, "spot_rate", "HQMCB63YR"),
    (63.5, "spot_rate", "HQMCB63Y6M"),
    (64, "spot_rate", "HQMCB64YR"),
    (64.5, "spot_rate", "HQMCB64Y6M"),
    (65, "spot_rate", "HQMCB65YR"),
    (65.5, "spot_rate", "HQMCB65Y6M"),
    (66, "spot_rate", "HQMCB66YR"),
    (66.5, "spot_rate", "HQMCB66Y6M"),
    (67, "spot_rate", "HQMCB67YR"),
    (67.5, "spot_rate", "HQMCB67Y6M"),
    (68, "spot_rate", "HQMCB68YR"),
    (68.5, "spot_rate", "HQMCB68Y6M"),
    (69, "spot_rate", "HQMCB69YR"),
    (69.5, "spot_rate", "HQMCB69Y6M"),
    (70, "spot_rate", "HQMCB70YR"),
    (70.5, "spot_rate", "HQMCB70Y6M"),
    (71, "spot_rate", "HQMCB71YR"),
    (71.5, "spot_rate", "HQMCB71Y6M"),
    (72, "spot_rate", "HQMCB72YR"),
    (72.5, "spot_rate", "HQMCB72Y6M"),
    (73, "spot_rate", "HQMCB73YR"),
    (73.5, "spot_rate", "HQMCB73Y6M"),
    (74, "spot_rate", "HQMCB74YR"),
    (74.5, "spot_rate", "HQMCB74Y6M"),
    (75, "spot_rate", "HQMCB75YR"),
    (75.5, "spot_rate", "HQMCB75Y6M"),
    (76, "spot_rate", "HQMCB76YR"),
    (76.5, "spot_rate", "HQMCB76Y6M"),
    (77, "spot_rate", "HQMCB77YR"),
    (77.5, "spot_rate", "HQMCB77Y6M"),
    (78, "spot_rate", "HQMCB78YR"),
    (78.5, "spot_rate", "HQMCB78Y6M"),
    (79, "spot_rate", "HQMCB79YR"),
    (79.5, "spot_rate", "HQMCB79Y6M"),
    (80, "spot_rate", "HQMCB80YR"),
    (80.5, "spot_rate", "HQMCB80Y6M"),
    (81, "spot_rate", "HQMCB81YR"),
    (81.5, "spot_rate", "HQMCB81Y6M"),
    (82, "spot_rate", "HQMCB82YR"),
    (82.5, "spot_rate", "HQMCB82Y6M"),
    (83, "spot_rate", "HQMCB83YR"),
    (83.5, "spot_rate", "HQMCB83Y6M"),
    (84, "spot_rate", "HQMCB84YR"),
    (84.5, "spot_rate", "HQMCB84Y6M"),
    (85, "spot_rate", "HQMCB85YR"),
    (85.5, "spot_rate", "HQMCB85Y6M"),
    (86, "spot_rate", "HQMCB86YR"),
    (86.5, "spot_rate", "HQMCB86Y6M"),
    (87, "spot_rate", "HQMCB87YR"),
    (87.5, "spot_rate", "HQMCB87Y6M"),
    (88, "spot_rate", "HQMCB88YR"),
    (88.5, "spot_rate", "HQMCB88Y6M"),
    (89, "spot_rate", "HQMCB89YR"),
    (89.5, "spot_rate", "HQMCB89Y6M"),
    (90, "spot_rate", "HQMCB90YR"),
    (90.5, "spot_rate", "HQMCB90Y6M"),
    (91, "spot_rate", "HQMCB91YR"),
    (91.5, "spot_rate", "HQMCB91Y6M"),
    (92, "spot_rate", "HQMCB92YR"),
    (92.5, "spot_rate", "HQMCB92Y6M"),
    (93, "spot_rate", "HQMCB93YR"),
    (93.5, "spot_rate", "HQMCB93Y6M"),
    (94, "spot_rate", "HQMCB94YR"),
    (94.5, "spot_rate", "HQMCB94Y6M"),
    (95, "spot_rate", "HQMCB95YR"),
    (95.5, "spot_rate", "HQMCB95Y6M"),
    (96, "spot_rate", "HQMCB96YR"),
    (96.5, "spot_rate", "HQMCB96Y6M"),
    (97, "spot_rate", "HQMCB97YR"),
    (97.5, "spot_rate", "HQMCB97Y6M"),
    (98, "spot_rate", "HQMCB98YR"),
    (98.5, "spot_rate", "HQMCB98Y6M"),
    (99, "spot_rate", "HQMCB99YR"),
    (99.5, "spot_rate", "HQMCB99Y6M"),
    (100, "spot_rate", "HQMCB100YR"),
)


def _select_series(maturity: float | str, category: str) -> list[str]:
    """Resolve (maturity, category) selectors to the matching FRED series ids.

    ``maturity`` may be a single float or a comma-separated string of floats;
    ``category`` is a comma-separated string of ``spot_rate``/``par_yield``.
    Mirrors the upstream filter: a catalog row matches when its maturity is in
    the requested set AND its category is in the requested set. Order follows
    the catalog (source-CSV order), de-duplicated.
    """
    tokens = maturity.split(",") if isinstance(maturity, str) else [maturity]
    maturities: list[float] = []
    for token in tokens:
        try:
            maturities.append(float(token))
        except (TypeError, ValueError):
            continue  # drop an unparseable maturity rather than 500
    categories = [c.strip() for c in category.split(",")]
    ids: list[str] = []
    for cat_maturity, cat_category, series_id in _CATALOG:
        in_selection = cat_maturity in maturities and cat_category in categories
        if in_selection and series_id not in ids:
            ids.append(series_id)
    return ids


class SugraSpotRateQueryParams(SpotRateQueryParams):
    """Sugra Spot Rate Query Parameters."""

    __json_schema_extra__ = {
        "maturity": {"multiple_items_allowed": True},
        "category": {
            "multiple_items_allowed": True,
            "choices": ["par_yield", "spot_rate"],
        },
    }


class SugraSpotRateData(SpotRateData):
    """Sugra Spot Rate Data."""


class SugraSpotRateFetcher(Fetcher[SugraSpotRateQueryParams, list[SugraSpotRateData]]):
    """Fetch HQM Corporate Bond spot rates / par yields (HQMCB* series) from Sugra."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraSpotRateQueryParams:
        """Transform the query parameters."""
        return SugraSpotRateQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraSpotRateQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the raw HQMCB series for the selected maturities/categories."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        ids = _select_series(query.maturity, query.category)
        if not ids:
            raise EmptyDataError(
                "No HQM Corporate Bond series match the requested "
                "maturity/category combination."
            )
        return await fred_series_payloads(
            api_key, ids, start_date=query.start_date, end_date=query.end_date
        )

    @staticmethod
    def transform_data(
        query: SugraSpotRateQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraSpotRateData]:
        """Melt the per-series observations into long (date, rate) rows.

        The rate is published AS-IS in percent (SpotRateData.rate carries no
        ``x-frontend_multiply``, so it is NOT divided by 100 - unlike the HQM
        yield-curve model on the same HQMCB series).
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows: list[dict] = []
        for payload in (data or {}).values():
            for obs in fred_observations(payload):
                rows.append({"date": obs["date"], "rate": obs["value"]})
        if not rows:
            raise EmptyDataError("No HQM Corporate Bond spot-rate observations returned.")
        rows.sort(key=lambda r: r["date"])
        return [SugraSpotRateData.model_validate(r) for r in rows]
