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
    "FamaFrenchFactors": {},
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


# --- Fama-French-specific regression tests (offline) ------------------------


def test_famafrench_to_iso_date_shapes():
    """Daily (YYYYMMDD), monthly (YYYYMM), and annual (YYYY) periods normalise."""
    from openbb_sugra.models.famafrench_factors import _to_iso_date

    assert _to_iso_date("20260430") == "2026-04-30"  # daily
    assert _to_iso_date("202604") == "2026-04-01"  # monthly
    assert _to_iso_date("2026") == "2026-12-31"  # annual


def test_famafrench_gates_raise_for_unserved_inputs():
    """Non-america regions and unserved factor/frequency combos raise clearly."""
    import asyncio

    from openbb_core.provider.utils.errors import EmptyDataError

    from openbb_sugra.models.famafrench_factors import SugraFamaFrenchFactorsFetcher

    creds = {"sugra_api_key": "unused"}
    with pytest.raises(EmptyDataError):
        asyncio.run(
            SugraFamaFrenchFactorsFetcher.aextract_data(
                SugraFamaFrenchFactorsFetcher.transform_query({"region": "europe"}), creds
            )
        )
    with pytest.raises(EmptyDataError):
        asyncio.run(
            SugraFamaFrenchFactorsFetcher.aextract_data(
                SugraFamaFrenchFactorsFetcher.transform_query(
                    {"factor": "3_factors", "frequency": "annual"}
                ),
                creds,
            )
        )


def test_famafrench_orders_ascending_and_keeps_boundary_month():
    """Rows sort ascending; a mid-month start_date keeps its (anchored) month."""
    from datetime import date

    from openbb_sugra.models.famafrench_factors import SugraFamaFrenchFactorsFetcher

    query = SugraFamaFrenchFactorsFetcher.transform_query(
        {"factor": "3_factors", "frequency": "monthly", "start_date": "2026-02-15"}
    )
    # Newest-first, like the Sugra API.
    data = [
        {"date": "202604", "Mkt-RF": 1.0, "SMB": 0.1, "HML": 0.2, "RF": 0.0},
        {"date": "202603", "Mkt-RF": 2.0, "SMB": 0.1, "HML": 0.2, "RF": 0.0},
        {"date": "202602", "Mkt-RF": 3.0, "SMB": 0.1, "HML": 0.2, "RF": 0.0},
        {"date": "202601", "Mkt-RF": 4.0, "SMB": 0.1, "HML": 0.2, "RF": 0.0},
    ]
    rows = SugraFamaFrenchFactorsFetcher.transform_data(query, data)
    dates = [r.date for r in rows]
    assert dates == sorted(dates)  # ascending
    assert dates[0] == date(2026, 2, 1)  # boundary month kept, January dropped


# --- Fama-French-specific regression tests (live) ---------------------------


def test_famafrench_momentum_and_daily_live(credentials):
    """Momentum column maps, daily path works, and history is not truncated to 60."""
    import asyncio

    from openbb_sugra.models.famafrench_factors import SugraFamaFrenchFactorsFetcher

    mom_q = SugraFamaFrenchFactorsFetcher.transform_query(
        {"factor": "momentum", "frequency": "monthly"}
    )
    mom = SugraFamaFrenchFactorsFetcher.transform_data(
        mom_q, asyncio.run(SugraFamaFrenchFactorsFetcher.aextract_data(mom_q, credentials))
    )
    assert mom and mom[0].mom is not None
    assert [r.date for r in mom] == sorted(r.date for r in mom)  # ascending

    daily_q = SugraFamaFrenchFactorsFetcher.transform_query(
        {"factor": "3_factors", "frequency": "daily"}
    )
    daily = SugraFamaFrenchFactorsFetcher.transform_data(
        daily_q,
        asyncio.run(SugraFamaFrenchFactorsFetcher.aextract_data(daily_q, credentials)),
    )
    assert len(daily) > 60  # full history requested, not just the trailing 60
