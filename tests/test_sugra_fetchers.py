"""Tests for the Sugra provider.

Two layers:

- Structural tests run everywhere with no network and no key: they prove the
  provider loads, every fetcher is wired to a real OpenBB standard-model key, and
  every fetcher implements the contract.
- The live integration test (one case per fetcher) runs only when
  ``SUGRA_TEST_API_KEY`` is set; it calls each fetcher against the Sugra API and
  asserts the full transform pipeline succeeds. This is the pre-publish gate.
"""

import inspect

import pytest
from openbb_core.app.provider_interface import ProviderInterface
from openbb_core.provider.abstract.fetcher import Fetcher

from openbb_sugra import sugra_provider

# One representative parameter set per fetcher (live data verified).
PARAMS: dict[str, dict] = {
    "AnalystEstimates": {"symbol": "AAPL"},
    "AvailableIndices": {},
    "BalanceSheet": {"symbol": "AAPL", "period": "annual"},
    "BlsSearch": {"query": "cpi"},
    "BlsSeries": {"symbol": "CPI-ALL"},
    "COT": {"code": "GOLD"},
    "COTSearch": {"query": "gold"},
    "CalendarDividend": {},
    "CalendarEarnings": {},
    "CalendarSplits": {},
    "CashFlowStatement": {"symbol": "AAPL", "period": "annual"},
    "CommoditySpotPrices": {},
    "CompanyFilings": {"symbol": "AAPL"},
    "CompanyNews": {"symbol": "AAPL"},
    "ConsumerPriceIndex": {},
    "CryptoHistorical": {"symbol": "BITCOIN"},
    "CryptoSearch": {"query": "bitcoin"},
    "CurrencyHistorical": {"symbol": "EURUSD"},
    "CurrencyPairs": {},
    "CurrencySnapshots": {},
    "EquityActive": {},
    "EquityAggressiveSmallCaps": {},
    "EquityGainers": {},
    "EquityHistorical": {"symbol": "AAPL"},
    "EquityInfo": {"symbol": "AAPL"},
    "EquityLosers": {},
    "EquityOwnership": {"symbol": "AAPL"},
    "EquityQuote": {"symbol": "AAPL"},
    "EquityScreener": {},
    "EquitySearch": {"query": "Apple"},
    "EquityUndervaluedGrowth": {},
    "EquityUndervaluedLargeCaps": {},
    "EtfHistorical": {"symbol": "SPY"},
    "EtfHoldings": {"symbol": "SPY"},
    "EtfInfo": {"symbol": "SPY"},
    "EtfPricePerformance": {"symbol": "SPY"},
    "EtfSearch": {"query": "SPY"},
    "FederalFundsRate": {},
    "FinancialRatios": {"symbol": "AAPL"},
    "Form13FHR": {"symbol": "0001067983"},
    "ForwardEbitdaEstimates": {"symbol": "AAPL"},
    "ForwardEpsEstimates": {"symbol": "AAPL"},
    "ForwardSalesEstimates": {"symbol": "AAPL"},
    "FredSearch": {"query": "unemployment"},
    "FredSeries": {"symbol": "GDP"},
    "GdpNominal": {},
    "GdpReal": {},
    "GrowthTechEquities": {},
    "HistoricalDividends": {"symbol": "AAPL"},
    "HistoricalSplits": {"symbol": "NVDA"},
    "IncomeStatement": {"symbol": "AAPL", "period": "annual"},
    "IndexConstituents": {"symbol": "^GSPC"},
    "IndexHistorical": {"symbol": "^GSPC"},
    "InsiderTrading": {"symbol": "AAPL"},
    "InstitutionalOwnership": {"symbol": "AAPL"},
    "KeyMetrics": {"symbol": "AAPL"},
    "MaritimeChokePointInfo": {},
    "MaritimeChokePointVolume": {},
    "MarketSnapshots": {},
    "MoneyMeasures": {},
    "NonFarmPayrolls": {},
    "OptionsChains": {"symbol": "AAPL"},
    "PersonalConsumptionExpenditures": {},
    "PetroleumStatusReport": {},
    "PortInfo": {},
    "PortVolume": {"port_id": "port1325", "limit": 50},
    "PricePerformance": {"symbol": "AAPL"},
    "PriceTargetConsensus": {"symbol": "AAPL"},
    "SOFR": {},
    "SONIA": {},
    "ShareStatistics": {"symbol": "AAPL"},
    "ShortTermEnergyOutlook": {},
    "TrailingDividendYield": {"symbol": "AAPL"},
    "Unemployment": {},
    "WorldNews": {},
}

FETCHERS = sorted(sugra_provider.fetcher_dict.items())


def test_provider_metadata():
    """The provider declares the expected name, credential, and entry shape."""
    assert sugra_provider.name == "sugra"
    assert sugra_provider.credentials == ["sugra_api_key"]
    assert sugra_provider.fetcher_dict, "no fetchers registered"


def test_every_fetcher_key_is_a_real_standard_model():
    """Every fetcher_dict key resolves to an OpenBB standard model."""
    valid = set(ProviderInterface().map.keys())
    unknown = [k for k in sugra_provider.fetcher_dict if k not in valid]
    assert not unknown, f"unknown standard-model keys: {unknown}"


def test_params_cover_every_fetcher():
    """Each registered fetcher has a live-test parameter set."""
    missing = [k for k in sugra_provider.fetcher_dict if k not in PARAMS]
    assert not missing, f"missing PARAMS for: {missing}"


@pytest.mark.parametrize("key,fetcher", FETCHERS, ids=[k for k, _ in FETCHERS])
def test_fetcher_implements_contract(key, fetcher):
    """Each fetcher subclasses Fetcher and implements the TET methods."""
    assert issubclass(fetcher, Fetcher)
    for method in ("transform_query", "transform_data"):
        assert callable(getattr(fetcher, method))
    assert callable(getattr(fetcher, "aextract_data", None)) or callable(
        getattr(fetcher, "extract_data", None)
    )
    assert inspect.iscoroutinefunction(fetcher.aextract_data)


@pytest.mark.parametrize("key,fetcher", FETCHERS, ids=[k for k, _ in FETCHERS])
def test_fetcher_returns_live_data(key, fetcher, credentials):
    """Live pre-publish gate: each fetcher returns real data from the Sugra API."""
    result = fetcher.test(PARAMS[key], credentials)
    assert result is None


# --- BLS-specific regression tests (offline) --------------------------------


def test_bls_to_iso_date_handles_every_period_shape():
    """Annual, monthly, and quarterly periods normalise; bad ones are skipped."""
    from openbb_sugra.models.bls_series import _to_iso_date

    assert _to_iso_date("2026-05") == "2026-05-01"  # monthly
    assert _to_iso_date("2026") == "2026-01-01"  # annual
    assert _to_iso_date("2026-Q01") == "2026-01-01"  # quarter 1
    assert _to_iso_date("2025-Q04") == "2025-10-01"  # quarter 4
    assert _to_iso_date("2026-Q2") == "2026-04-01"  # short-form quarter
    assert _to_iso_date("2026-13") is None  # out-of-range month
    assert _to_iso_date("2026-Q05") is None  # out-of-range quarter
    assert _to_iso_date("not-a-date") is None


def test_bls_search_semicolon_is_an_and_operator():
    """';' splits into terms that must ALL match (key or name), not a literal."""
    from openbb_sugra.models.bls_search import (
        SugraBlsSearchFetcher,
        SugraBlsSearchQueryParams,
    )

    catalog = [
        {"key": "cpi-all", "name": "CPI All Urban Consumers"},
        {"key": "cpi-core", "name": "CPI Core"},
        {"key": "unemployment", "name": "Unemployment Rate"},
    ]
    rows = SugraBlsSearchFetcher.transform_data(
        SugraBlsSearchQueryParams(query="cpi;urban"), catalog
    )
    assert {r.symbol for r in rows} == {"cpi-all"}


# --- BLS-specific regression tests (live) -----------------------------------


def test_bls_series_quarterly_productivity(credentials):
    """The quarterly 'productivity' series (YYYY-Q0N dates) must not crash."""
    from openbb_sugra.models.bls_series import SugraBlsSeriesFetcher

    assert SugraBlsSeriesFetcher.test({"symbol": "PRODUCTIVITY"}, credentials) is None


def test_bls_series_date_window_is_honored(credentials):
    """start_date/end_date bound the returned observations (client-side filter)."""
    import asyncio
    from datetime import date

    from openbb_sugra.models.bls_series import SugraBlsSeriesFetcher

    query = SugraBlsSeriesFetcher.transform_query(
        {"symbol": "CPI-ALL", "start_date": "2025-01-01", "end_date": "2025-06-30"}
    )
    data = asyncio.run(SugraBlsSeriesFetcher.aextract_data(query, credentials))
    rows = SugraBlsSeriesFetcher.transform_data(query, data)
    assert rows
    assert all(date(2025, 1, 1) <= row.date <= date(2025, 6, 30) for row in rows)
