"""Sugra Currency Reference Rates Model."""

# pylint: disable=unused-argument

from typing import Any

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.currency_reference_rates import (
    CurrencyReferenceRatesData,
    CurrencyReferenceRatesQueryParams,
)

# The standard model is a single wide row: `date` plus one column per currency.
# Derive the valid currency columns from the model so an unexpected key in the
# upstream payload is dropped rather than carried as an untyped extra.
_CURRENCY_FIELDS = set(CurrencyReferenceRatesData.model_fields) - {"date"}


class SugraCurrencyReferenceRatesFetcher(
    Fetcher[CurrencyReferenceRatesQueryParams, list[CurrencyReferenceRatesData]]
):
    """Fetch ECB Euro foreign-exchange reference rates from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> CurrencyReferenceRatesQueryParams:
        """Transform the query parameters."""
        return CurrencyReferenceRatesQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: CurrencyReferenceRatesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the latest ECB reference-rate snapshot from the Sugra API.

        `/api/v1/forex/latest` surfaces ECB Euro reference rates (via the
        Frankfurter priority-1 connector source). No `symbols` param is sent so
        the full currency set is returned to populate every model column.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

        api_key = get_api_key(credentials)
        response = await sugra_get("/api/v1/forex/latest", api_key)
        payload = envelope_data(response)
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def transform_data(
        query: CurrencyReferenceRatesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[CurrencyReferenceRatesData]:
        """Reshape the rates map into the model's single wide reference-rate row."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        base = (data or {}).get("base")
        ref_date = (data or {}).get("date")
        rates = (data or {}).get("rates") or {}

        # `/forex/latest` has a non-ECB fallback chain (USD-based exchangerate-api,
        # then Bank of Russia). Those are not ECB reference rates - and a non-EUR
        # base would make EUR=1.0 and the row's semantics wrong - so refuse to
        # emit a mislabelled reference-rate row.
        if base != "EUR":
            raise EmptyDataError(
                "Sugra forex feed returned a non-ECB fallback "
                f"(base={base!r}); no ECB reference rates available."
            )
        if not ref_date or not rates:
            raise EmptyDataError("No ECB reference rates returned.")

        row: dict[str, Any] = {"date": ref_date, "EUR": 1.0}
        for currency, rate in rates.items():
            if rate is not None and currency in _CURRENCY_FIELDS:
                row[currency] = rate

        return [CurrencyReferenceRatesData.model_validate(row)]
