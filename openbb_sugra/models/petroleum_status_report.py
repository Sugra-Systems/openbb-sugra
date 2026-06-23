"""Sugra Petroleum Status Report Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.petroleum_status_report import (
    PetroleumStatusReportData,
    PetroleumStatusReportQueryParams,
)


class SugraPetroleumStatusReportQueryParams(PetroleumStatusReportQueryParams):
    """Sugra Petroleum Status Report Query Parameters."""


class SugraPetroleumStatusReportData(PetroleumStatusReportData):
    """Sugra Petroleum Status Report Data."""


def _in_window(date_str: str, start: Any | None, end: Any | None) -> bool:
    """Return True if the date string falls within the optional window."""
    if start and date_str < start.strftime("%Y-%m-%d"):
        return False
    return not (end and date_str > end.strftime("%Y-%m-%d"))


class SugraPetroleumStatusReportFetcher(
    Fetcher[
        SugraPetroleumStatusReportQueryParams,
        list[SugraPetroleumStatusReportData],
    ]
):
    """Fetch the EIA-style petroleum status report from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraPetroleumStatusReportQueryParams:
        """Transform the query parameters."""
        return SugraPetroleumStatusReportQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraPetroleumStatusReportQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return raw petroleum prices and stocks from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        import asyncio

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        prices_resp, stocks_resp = await asyncio.gather(
            sugra_get("/api/v1/commodities/energy/petroleum", api_key),
            sugra_get("/api/v1/commodities/energy/petroleum-stocks", api_key),
        )
        return {
            "prices": envelope_data(prices_resp),
            "stocks": envelope_data(stocks_resp),
        }

    @staticmethod
    def transform_data(
        query: SugraPetroleumStatusReportQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraPetroleumStatusReportData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        rows: list[SugraPetroleumStatusReportData] = []
        for table_key, block in (
            ("prices", data.get("prices") or {}),
            ("stocks", data.get("stocks") or {}),
        ):
            if not isinstance(block, dict):
                continue
            unit = block.get("unit")
            table_name = block.get("commodity") or table_key
            series = block.get("series") or {}
            for symbol, observations in series.items():
                if not isinstance(observations, list):
                    continue
                for order, obs in enumerate(observations):
                    date_str = obs.get("date")
                    value = obs.get("value")
                    if date_str is None or value is None:
                        continue
                    if not _in_window(date_str, query.start_date, query.end_date):
                        continue
                    rows.append(
                        SugraPetroleumStatusReportData.model_validate(
                            {
                                "date": date_str,
                                "table": table_name,
                                "symbol": symbol,
                                "order": order,
                                "title": symbol.replace("_", " ").title(),
                                "value": value,
                                "unit": unit,
                            }
                        )
                    )
        if not rows:
            raise EmptyDataError("No petroleum status report data returned.")
        return rows
