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
    "TreasuryAuctions": {"security_type": "note", "page_size": 10},
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


# --- Treasury auctions (DATA-17.8) ----------------------------------------

def test_treasury_auctions_maps_fields_and_skips_incomplete_rows():
    """Maps the Sugra projection to the standard model; a row missing the
    required issue_date/maturity_date is skipped, not failed."""
    from openbb_core.provider.standard_models.treasury_auctions import (
        USTreasuryAuctionsQueryParams,
    )

    from openbb_sugra.models.treasury_auctions import SugraUSTreasuryAuctionsFetcher

    data = [
        {
            "cusip": "91282CXX0", "security_type": "Note", "security_term": "5-Year",
            "issue_date": "2026-06-30", "maturity_date": "2031-06-30",
            "auction_date": "2026-06-24", "interest_rate": 4.125,
            "high_yield": "4.125", "bid_to_cover_ratio": "2.45",
            "offering_amt": "70000000000", "total_accepted": "70000000000",
            "allocation_method": "Single-Price", "allocation_pctage": 55.5,
        },
        # missing maturity_date -> required by the model, must be skipped
        {"cusip": "X", "security_type": "Bill", "security_term": "8-Week",
         "issue_date": "2026-06-25", "auction_date": "2026-06-23"},
    ]
    rows = SugraUSTreasuryAuctionsFetcher.transform_data(
        USTreasuryAuctionsQueryParams(), data
    )
    assert len(rows) == 1
    r = rows[0]
    assert str(r.cusip) == "91282CXX0"
    assert str(r.issue_date) == "2026-06-30"
    assert str(r.maturity_date) == "2031-06-30"
    assert r.high_yield == 4.125
    assert r.offering_amount == 70000000000.0
    assert r.auction_format == "Single-Price"
    assert r.allocation_percentage == 55.5


def test_treasury_auctions_client_side_cusip_and_date_filter():
    """cusip + start/end_date are applied client-side (the endpoint ignores them).

    Note: USTreasuryAuctionsQueryParams defaults the date window to ~the last 3
    months, so the cusip case uses a wide explicit start_date to isolate the
    cusip filter, and the date case sets an explicit window.
    """
    from datetime import date

    from openbb_core.provider.standard_models.treasury_auctions import (
        USTreasuryAuctionsQueryParams,
    )

    from openbb_sugra.models.treasury_auctions import SugraUSTreasuryAuctionsFetcher

    base = {
        "security_type": "Note", "security_term": "5-Year",
        "issue_date": "2026-06-30", "maturity_date": "2031-06-30",
    }
    data = [
        {**base, "cusip": "912828AA1", "auction_date": "2026-06-20"},
        {**base, "cusip": "912828BB2", "auction_date": "2026-01-10"},
    ]
    # Wide window so only the cusip filter applies (default window is ~3 months).
    by_cusip = SugraUSTreasuryAuctionsFetcher.transform_data(
        USTreasuryAuctionsQueryParams(cusip="912828bb2", start_date=date(2000, 1, 1)),
        data,
    )
    assert len(by_cusip) == 1 and str(by_cusip[0].cusip) == "912828BB2"

    by_date = SugraUSTreasuryAuctionsFetcher.transform_data(
        USTreasuryAuctionsQueryParams(start_date=date(2026, 6, 1), end_date=date(2026, 6, 30)),
        data,
    )
    assert len(by_date) == 1 and str(by_date[0].cusip) == "912828AA1"


def test_treasury_auctions_rejects_page_num_pagination():
    """The Sugra endpoint has no page offset; page_num>1 must raise, not mislead."""
    import asyncio

    from openbb_core.app.model.abstract.error import OpenBBError
    from openbb_core.provider.standard_models.treasury_auctions import (
        USTreasuryAuctionsQueryParams,
    )

    from openbb_sugra.models.treasury_auctions import SugraUSTreasuryAuctionsFetcher

    q = USTreasuryAuctionsQueryParams(page_num=2)
    try:
        asyncio.run(SugraUSTreasuryAuctionsFetcher.aextract_data(q, {"sugra_api_key": "x"}))
    except OpenBBError:
        return
    raise AssertionError("page_num>1 should raise OpenBBError")


def test_treasury_auctions_normalizes_security_type_and_flags_all_rejected():
    """Lowercase security_type from the endpoint is normalized to the model's
    title-case Literal; if every returned row fails validation the error says so
    (rather than conflating it with an empty filter match)."""
    from openbb_core.provider.standard_models.treasury_auctions import (
        USTreasuryAuctionsQueryParams,
    )
    from openbb_core.provider.utils.errors import EmptyDataError

    from openbb_sugra.models.treasury_auctions import SugraUSTreasuryAuctionsFetcher

    # A lowercase security_type would fail the title-case Literal without the
    # response-side normalization.
    ok = SugraUSTreasuryAuctionsFetcher.transform_data(
        USTreasuryAuctionsQueryParams(),
        [{
            "cusip": "91282CXX0", "security_type": "note", "security_term": "5-Year",
            "issue_date": "2026-06-30", "maturity_date": "2031-06-30",
            "auction_date": "2026-06-24",
        }],
    )
    assert len(ok) == 1 and ok[0].security_type == "Note"

    # Every row present but invalid (malformed issue_date passes the presence
    # check but fails date coercion) -> distinct validation error, not the
    # generic "nothing matched the query".
    try:
        SugraUSTreasuryAuctionsFetcher.transform_data(
            USTreasuryAuctionsQueryParams(),
            [{
                "cusip": "91282CXX0", "security_type": "Note", "security_term": "5-Year",
                "issue_date": "not-a-date", "maturity_date": "2031-06-30",
                "auction_date": "2026-06-24",
            }],
        )
    except EmptyDataError as exc:
        assert "failed standard-model validation" in str(exc)
        return
    raise AssertionError("all-invalid rows should raise EmptyDataError")
