"""Sugra Institutions Search Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_sec.models.institutions_search import (
    SecInstitutionsSearchData,
    SecInstitutionsSearchQueryParams,
)
from pydantic import Field


class SugraInstitutionsSearchQueryParams(SecInstitutionsSearchQueryParams):
    """Sugra Institutions Search Query Parameters.

    The Sugra advisers-search endpoint requires a ``query`` of at least two
    characters (it matches the term against adviser names); a shorter query
    raises a clear error rather than returning the full adviser universe.
    """


class SugraInstitutionsSearchData(SecInstitutionsSearchData):
    """Sugra Institutions Search Data."""

    crd: str | None = Field(default=None, description="The adviser's CRD number.")
    sec_number: str | None = Field(default=None, description="The SEC registration number.")
    legal_name: str | None = Field(default=None, description="The legal name of the institution.")
    firm_type: str | None = Field(default=None, description="The firm registration type.")
    raum_total: float | None = Field(
        default=None,
        description="Total regulatory assets under management (USD).",
    )


class SugraInstitutionsSearchFetcher(
    Fetcher[SugraInstitutionsSearchQueryParams, list[SugraInstitutionsSearchData]]
):
    """Search SEC-registered investment advisers (institutions) via the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraInstitutionsSearchQueryParams:
        """Transform the query parameters."""
        return SugraInstitutionsSearchQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraInstitutionsSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return raw adviser rows from the Sugra SEC advisers-search endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError

        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        # The endpoint takes ``q`` (not ``query``) and requires >= 2 characters;
        # guard locally so a short query gives a clear message instead of an
        # opaque upstream 422 -> EmptyDataError.
        term = (query.query or "").strip()
        if len(term) < 2:
            raise OpenBBError(
                "Institutions search requires a query of at least two characters"
                f" (e.g. 'blackrock', 'vanguard') - got {term!r}."
            )

        api_key = get_api_key(credentials)
        response = await sugra_get(
            "/api/v1/sec/advisers/search", api_key, {"q": term}
        )
        payload = envelope_data(response)
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        return rows or []

    @staticmethod
    def transform_data(
        query: SugraInstitutionsSearchQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[SugraInstitutionsSearchData]:
        """Validate and transform into the standard model."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        if not data:
            raise EmptyDataError("No SEC institutions returned.")

        results: list[SugraInstitutionsSearchData] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not name:
                continue
            cik = item.get("cik")
            crd = item.get("crd")
            raum = item.get("raum_total")
            results.append(
                SugraInstitutionsSearchData(
                    name=name,
                    cik=None if cik is None else str(cik),
                    crd=None if crd is None else str(crd),
                    sec_number=item.get("sec_number"),
                    legal_name=item.get("legal_name"),
                    firm_type=item.get("firm_type"),
                    raum_total=None if raum is None else float(raum),
                )
            )

        if not results:
            raise EmptyDataError("No institution rows produced.")
        return results
