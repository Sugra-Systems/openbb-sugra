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
    "CongressAmendments": {"congress": 119, "limit": 5},
    "CongressBills": {"congress": 119, "limit": 5},
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


# --- Congress-specific regression tests (offline) ---------------------------


def test_congress_bills_null_latest_action_does_not_crash():
    """A placeholder bill with latestAction:null maps to latest_action=None."""
    from openbb_sugra.models.congress_bills import SugraCongressBillsFetcher

    query = SugraCongressBillsFetcher.transform_query({})
    data = [
        {
            "congress": 119,
            "number": "6",
            "type": "HR",
            "title": "Reserved for the Speaker.",
            "originChamber": "House",
            "originChamberCode": "H",
            "url": "https://api.congress.gov/v3/bill/119/hr/6?format=json",
            "updateDate": "2025-01-14",
            "latestAction": None,
        }
    ]
    rows = SugraCongressBillsFetcher.transform_data(query, data)
    assert len(rows) == 1
    assert rows[0].latest_action is None


def test_congress_amendment_type_filter_drops_other_types():
    """A requested amendment_type keeps only rows of that type (Sugra ignores it)."""
    from openbb_sugra.models.congress_amendments import SugraCongressAmendmentsFetcher

    query = SugraCongressAmendmentsFetcher.transform_query(
        {"congress": 119, "amendment_type": "samdt"}
    )
    data = [
        {"congress": 119, "number": "1", "type": "HAMDT",
         "updateDate": "2025-01-02T00:00:00Z", "url": "https://x/1"},
        {"congress": 119, "number": "2", "type": "SAMDT",
         "updateDate": "2025-01-01T00:00:00Z", "url": "https://x/2"},
    ]
    rows = SugraCongressAmendmentsFetcher.transform_data(query, data)
    assert {r.amendment_type for r in rows} == {"SAMDT"}


def test_congress_rejects_offset_and_unbounded_limit():
    """offset>0 and limit=0 are unsupported by Sugra and raise, not mislead."""
    import asyncio

    from openbb_core.app.model.abstract.error import OpenBBError

    from openbb_sugra.models.congress_bills import SugraCongressBillsFetcher

    creds = {"sugra_api_key": "unused"}
    with pytest.raises(OpenBBError):
        asyncio.run(
            SugraCongressBillsFetcher.aextract_data(
                SugraCongressBillsFetcher.transform_query({"offset": 5}), creds
            )
        )
    with pytest.raises(OpenBBError):
        asyncio.run(
            SugraCongressBillsFetcher.aextract_data(
                SugraCongressBillsFetcher.transform_query(
                    {"bill_type": "hr", "limit": 0}
                ),
                creds,
            )
        )


def test_congress_bills_date_window_filters_offline():
    """start_date/end_date drop bills updated outside the window (client-side)."""
    from openbb_sugra.models.congress_bills import SugraCongressBillsFetcher

    def _bill(number: str, updated: str) -> dict:
        return {
            "congress": 119,
            "number": number,
            "type": "HR",
            "title": f"Bill {number}",
            "originChamber": "House",
            "originChamberCode": "H",
            "url": f"https://api.congress.gov/v3/bill/119/hr/{number}?format=json",
            "updateDate": updated,
            "latestAction": None,
        }

    query = SugraCongressBillsFetcher.transform_query(
        {"start_date": "2025-01-01", "end_date": "2025-01-31"}
    )
    data = [
        _bill("6", "2025-01-14"),  # inside
        _bill("7", "2025-02-20"),  # after window
        _bill("8", "2024-12-30"),  # before window
    ]
    rows = SugraCongressBillsFetcher.transform_data(query, data)
    assert {r.bill_number for r in rows} == {6}
