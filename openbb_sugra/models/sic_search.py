"""Sugra SEC SIC Search Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_sec.models.sic_search import SecSicSearchData, SecSicSearchQueryParams
from pydantic import Field


class SugraSicSearchQueryParams(SecSicSearchQueryParams):
    """Sugra SEC SIC Search Query Parameters.

    Drops the ``use_cache`` field of the SEC provider: the catalog is embedded
    in the package, so there is no remote table to cache.
    """

    use_cache: bool | None = Field(default=None, exclude=True, description="Unused.")


class SugraSicSearchData(SecSicSearchData):
    """Sugra SEC SIC Search Data."""


class SugraSicSearchFetcher(
    Fetcher[SugraSicSearchQueryParams, list[SugraSicSearchData]]
):
    """Search the SEC Standard Industrial Classification (SIC) code list.

    The SIC code list is a small, static SEC reference table, so it is embedded
    in the package (``openbb_sugra.utils.sic_catalog``) and filtered in-process -
    no Sugra endpoint or network call is involved. The query is matched, case
    insensitive, as a substring against the SIC code, industry title, and office,
    exactly as the standard SEC provider matches against the live table.
    """

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraSicSearchQueryParams:
        """Transform the query parameters."""
        return SugraSicSearchQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraSicSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Filter the embedded SIC catalog by the query substring."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.sic_catalog import SIC_CODES

        term = (query.query or "").strip().lower()
        if not term:
            return list(SIC_CODES)
        return [
            row
            for row in SIC_CODES
            if term in str(row["sic"]).lower()
            or term in row["industry"].lower()
            or term in row["office"].lower()
        ]

    @staticmethod
    def transform_data(
        query: SugraSicSearchQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraSicSearchData]:
        """Validate the filtered rows into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError(
                f"No SIC codes matched the query '{query.query}'."
            )
        return [SugraSicSearchData.model_validate(row) for row in data]
