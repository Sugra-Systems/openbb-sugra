"""Sugra Money Measures Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.money_measures import (
    MoneyMeasuresData,
    MoneyMeasuresQueryParams,
)

_M1_SERIES = "M1SL"
_M2_SERIES = "M2SL"


class SugraMoneyMeasuresQueryParams(MoneyMeasuresQueryParams):
    """Sugra Money Measures Query Parameters."""


class SugraMoneyMeasuresData(MoneyMeasuresData):
    """Sugra Money Measures Data."""


def _observations(payload: Any) -> dict[str, float]:
    """Return {date: value} from a FRED series payload, dropping null/'.'."""
    out: dict[str, float] = {}
    obs = (payload or {}).get("observations") or [] if isinstance(payload, dict) else []
    for row in obs:
        if not isinstance(row, dict) or row.get("date") is None:
            continue
        value = row.get("value")
        if isinstance(value, str):
            if value.strip() in {"", "."}:
                continue
            value = float(value)
        if value is None:
            continue
        out[str(row["date"])] = value
    return out


class SugraMoneyMeasuresFetcher(
    Fetcher[SugraMoneyMeasuresQueryParams, list[SugraMoneyMeasuresData]]
):
    """Fetch M1 and M2 money supply (M1SL, M2SL) from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraMoneyMeasuresQueryParams:
        """Transform the query parameters."""
        return SugraMoneyMeasuresQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraMoneyMeasuresQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the merged M1/M2 series from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        import asyncio

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        params: dict[str, Any] = {}
        if query.start_date:
            params["observation_start"] = str(query.start_date)
        if query.end_date:
            params["observation_end"] = str(query.end_date)
        m1_resp, m2_resp = await asyncio.gather(
            sugra_get(f"/api/v1/fred/series/{_M1_SERIES}", api_key, params),
            sugra_get(f"/api/v1/fred/series/{_M2_SERIES}", api_key, params),
        )
        return {
            "m1": envelope_data(m1_resp),
            "m2": envelope_data(m2_resp),
        }

    @staticmethod
    def transform_data(
        query: SugraMoneyMeasuresQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraMoneyMeasuresData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        m1 = _observations((data or {}).get("m1"))
        m2 = _observations((data or {}).get("m2"))
        common = sorted(set(m1) & set(m2))
        if not common:
            raise EmptyDataError("No overlapping M1/M2 observations to satisfy required fields.")
        rows: list[SugraMoneyMeasuresData] = []
        for month in common:
            rows.append(
                SugraMoneyMeasuresData.model_validate(
                    {"month": month, "m1": m1[month], "m2": m2[month]}
                )
            )
        return rows
