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
    "BalanceOfPayments": {"report_type": "main"},
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
    "CongressAmendmentInfo": {"amendment_url": "118/samdt/1052"},
    "CongressAmendments": {"congress": 119, "limit": 5},
    "CongressBillInfo": {"bill_url": "119/hr/1"},
    "CongressBills": {"congress": 119, "limit": 5},
    "ConsumerPriceIndex": {},
    "CryptoHistorical": {"symbol": "BITCOIN"},
    "CryptoSearch": {"query": "bitcoin"},
    "CurrencyHistorical": {"symbol": "EURUSD"},
    "CurrencyPairs": {},
    "CurrencyReferenceRates": {},
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
    "FamaFrenchBreakpoints": {"breakpoint_type": "me"},
    "FamaFrenchCountryPortfolioReturns": {"country": "united_kingdom"},
    "FamaFrenchFactors": {},
    "FamaFrenchInternationalIndexReturns": {"index": "all"},
    "FamaFrenchRegionalPortfolioReturns": {"portfolio": "developed_6_portfolios_me_be-me"},
    "FamaFrenchUSPortfolioReturns": {"portfolio": "portfolios_formed_on_me"},
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
    "YieldCurve": {},
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


def test_congress_bill_info_parses_bill_ref_forms():
    """bill_url accepts a bare ref, a leading-slashed ref, and a full URL."""
    from openbb_sugra.models.congress_bill_info import _parse_bill_ref

    assert _parse_bill_ref("119/hr/1") == (119, "hr", "1")
    assert _parse_bill_ref("/119/s/1") == (119, "s", "1")
    assert _parse_bill_ref("118/HR/3684") == (118, "hr", "3684")
    assert _parse_bill_ref(
        "https://api.congress.gov/v3/bill/119/s/1947?format=json"
    ) == (119, "s", "1947")


def test_congress_bill_info_rejects_unparseable_ref():
    """A ref without congress/type/number raises rather than guessing."""
    from openbb_core.app.model.abstract.error import OpenBBError

    from openbb_sugra.models.congress_bill_info import _parse_bill_ref

    with pytest.raises(OpenBBError):
        _parse_bill_ref("not-a-bill")


def test_congress_bill_info_transform_builds_markdown():
    """A spliced bill (sub-resources already inlined) renders the canonical markdown."""
    from openbb_sugra.models.congress_bill_info import SugraCongressBillInfoFetcher

    query = SugraCongressBillInfoFetcher.transform_query({"bill_url": "119/hr/1"})
    bill = {
        "congress": 119, "number": "1", "type": "HR", "title": "Test Act",
        "originChamber": "House", "introducedDate": "2025-01-03",
        "updateDate": "2025-02-01",
        "latestAction": {"actionDate": "2025-02-01", "text": "Referred"},
        "sponsors": [{"fullName": "Rep. Example"}],
        "actions": [{"actionDate": "2025-01-03", "text": "Introduced", "type": "IntroReferral"}],
        "subjects": [{"name": "Health"}],
        "relatedBills": [{"congress": 119, "type": "S", "number": 9, "title": "Companion"}],
    }
    out = SugraCongressBillInfoFetcher.transform_data(query, bill)
    assert out.markdown_content.startswith("## Test Act")
    assert "### Actions" in out.markdown_content
    assert "### Subjects" in out.markdown_content
    assert "### Related Bills" in out.markdown_content
    assert out.raw_data["title"] == "Test Act"


def test_congress_amendment_info_parses_ref_forms():
    """amendment_url accepts a bare ref, a leading-slashed ref, and a full URL."""
    from openbb_sugra.models.congress_amendment_info import _parse_amendment_ref

    assert _parse_amendment_ref("119/hamdt/2") == (119, "hamdt", "2")
    assert _parse_amendment_ref("/118/samdt/1052") == (118, "samdt", "1052")
    assert _parse_amendment_ref(
        "https://api.congress.gov/v3/amendment/119/hamdt/2?format=json"
    ) == (119, "hamdt", "2")


def test_congress_amendment_info_rejects_unparseable_ref():
    """A ref without congress/type/number raises rather than guessing."""
    from openbb_core.app.model.abstract.error import OpenBBError

    from openbb_sugra.models.congress_amendment_info import _parse_amendment_ref

    with pytest.raises(OpenBBError):
        _parse_amendment_ref("not-an-amendment")


def test_congress_amendment_info_transform_builds_markdown():
    """A spliced amendment (sub-resources already inlined) renders the canonical markdown."""
    from openbb_sugra.models.congress_amendment_info import SugraCongressAmendmentInfoFetcher

    query = SugraCongressAmendmentInfoFetcher.transform_query({"amendment_url": "118/samdt/1052"})
    amendment = {
        "congress": 118, "number": "1052", "type": "SAMDT",
        "description": "An amendment to strike a section.", "updateDate": "2024-01-15",
        "amendedBill": {"congress": 118, "type": "S", "number": "1", "title": "A Bill"},
        "sponsors": [{"fullName": "Sen. Example"}],
        "actions": [{"actionDate": "2024-01-10", "text": "Submitted", "type": "Floor"}],
        "cosponsors": [{"fullName": "Sen. Two"}],
    }
    out = SugraCongressAmendmentInfoFetcher.transform_data(query, amendment)
    assert "### Amended Bill" in out.markdown_content
    assert "### Actions" in out.markdown_content
    assert out.raw_data["number"] == "1052"


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


# --- Fama-French portfolios / breakpoints (DATA-17.10) ---------------------

def test_us_portfolio_melts_wide_records_to_long():
    """The Sugra API returns wide records (one column per formation); the fetcher
    melts them to the standard long (date, portfolio, measure, value) shape,
    orders ascending, and echoes the queried measure."""
    from openbb_sugra.models.famafrench_us_portfolio_returns import (
        SugraFamaFrenchUSPortfolioReturnsFetcher,
    )

    query = SugraFamaFrenchUSPortfolioReturnsFetcher.transform_query(
        {"portfolio": "portfolios_formed_on_me", "measure": "value"}
    )
    # Newest-first wide records, as the Sugra API serves them.
    data = [
        {"date": "192608", "Lo 30": 3.0, "Hi 30": 4.0},
        {"date": "192607", "Lo 30": 1.0, "Hi 30": 2.0},
    ]
    rows = SugraFamaFrenchUSPortfolioReturnsFetcher.transform_data(query, data)
    assert len(rows) == 4  # 2 periods x 2 formations
    # ascending by (date, portfolio)
    assert [(str(r.date), r.portfolio, r.value) for r in rows] == [
        ("1926-07-01", "Hi 30", 2.0),
        ("1926-07-01", "Lo 30", 1.0),
        ("1926-08-01", "Hi 30", 4.0),
        ("1926-08-01", "Lo 30", 3.0),
    ]
    assert all(r.measure == "value" for r in rows)


def test_us_portfolio_windows_by_date_and_skips_none_cells():
    from openbb_sugra.models.famafrench_us_portfolio_returns import (
        SugraFamaFrenchUSPortfolioReturnsFetcher,
    )

    query = SugraFamaFrenchUSPortfolioReturnsFetcher.transform_query(
        {"portfolio": "portfolios_formed_on_me", "measure": "value",
         "start_date": "1926-08-01"}
    )
    data = [
        {"date": "192608", "Lo 30": 3.0, "Hi 30": None},  # None cell dropped
        {"date": "192607", "Lo 30": 1.0, "Hi 30": 2.0},   # before start -> dropped
    ]
    rows = SugraFamaFrenchUSPortfolioReturnsFetcher.transform_data(query, data)
    assert [(str(r.date), r.portfolio) for r in rows] == [("1926-08-01", "Lo 30")]


def test_breakpoint_date_anchors_to_month_end():
    """Monthly breakpoint tokens anchor to MONTH END (matching the upstream
    provider), annual ratio tokens to year end."""
    from openbb_sugra.models.famafrench_breakpoints import _breakpoint_date_to_iso

    assert _breakpoint_date_to_iso("202602") == "2026-02-28"
    assert _breakpoint_date_to_iso("202604") == "2026-04-30"
    assert _breakpoint_date_to_iso("202612") == "2026-12-31"
    assert _breakpoint_date_to_iso("2025") == "2025-12-31"


def test_breakpoints_validate_ratio_two_count_columns():
    from openbb_sugra.models.famafrench_breakpoints import (
        SugraFamaFrenchBreakpointFetcher,
    )

    query = SugraFamaFrenchBreakpointFetcher.transform_query(
        {"breakpoint_type": "be-me"}
    )
    pcts = {f"percentile_{p}": float(p) for p in range(5, 101, 5)}
    data = [{"date": "1927", "num_firms_less_than_0": 1,
             "num_firms_greater_than_0": 464, **pcts}]
    rows = SugraFamaFrenchBreakpointFetcher.transform_data(query, data)
    assert len(rows) == 1
    assert str(rows[0].date) == "1927-12-31"
    assert rows[0].num_firms_less_than_0 == 1
    assert rows[0].num_firms_greater_than_0 == 464
    assert rows[0].num_firms is None


# --- Fama-French international country / index (DATA-17.10.1) ---------------

def test_country_portfolio_validates_flat_records_one_row_per_period():
    """The Sugra API returns flat snake-cased records (one per period); the country
    fetcher validates each directly into the model (no melt), normalises the period
    token to month-start, and orders ascending."""
    from openbb_sugra.models.famafrench_country_portfolio_returns import (
        SugraFamaFrenchCountryPortfolioReturnsFetcher,
    )

    query = SugraFamaFrenchCountryPortfolioReturnsFetcher.transform_query(
        {"country": "united_kingdom", "measure": "usd"}
    )
    # Newest-first wide records, as the Sugra API serves them.
    data = [
        {"date": "197502", "mkt": 11.0, "be_me_high": 12.0, "yld_low": 19.0},
        {"date": "197501", "mkt": 1.0, "be_me_high": 2.0, "yld_low": 9.0},
    ]
    rows = SugraFamaFrenchCountryPortfolioReturnsFetcher.transform_data(query, data)
    assert [(str(r.date), r.mkt, r.be_me_high) for r in rows] == [
        ("1975-01-01", 1.0, 2.0),
        ("1975-02-01", 11.0, 12.0),
    ]


def test_country_portfolio_ratios_keep_int_firms_and_window():
    from openbb_sugra.models.famafrench_country_portfolio_returns import (
        SugraFamaFrenchCountryPortfolioReturnsFetcher,
    )

    query = SugraFamaFrenchCountryPortfolioReturnsFetcher.transform_query(
        {"country": "united_kingdom", "measure": "ratios", "start_date": "1976-01-01"}
    )
    data = [
        {"date": "1976", "firms": 200, "bm": 1.5, "ep": 1.6},
        {"date": "1975", "firms": 100, "bm": 0.5, "ep": 0.6},  # before start -> dropped
    ]
    rows = SugraFamaFrenchCountryPortfolioReturnsFetcher.transform_data(query, data)
    assert len(rows) == 1
    assert str(rows[0].date) == "1976-12-31"
    assert rows[0].firms == 200 and isinstance(rows[0].firms, int)


def test_country_portfolio_empty_raises():
    from openbb_core.provider.utils.errors import EmptyDataError

    from openbb_sugra.models.famafrench_country_portfolio_returns import (
        SugraFamaFrenchCountryPortfolioReturnsFetcher,
    )

    query = SugraFamaFrenchCountryPortfolioReturnsFetcher.transform_query(
        {"country": "united_kingdom"}
    )
    with pytest.raises(EmptyDataError):
        SugraFamaFrenchCountryPortfolioReturnsFetcher.transform_data(query, [])


def test_international_index_validates_flat_records():
    from openbb_sugra.models.famafrench_international_index_returns import (
        SugraFamaFrenchInternationalIndexReturnsFetcher,
    )

    query = SugraFamaFrenchInternationalIndexReturnsFetcher.transform_query(
        {"index": "all", "measure": "usd"}
    )
    data = [
        {"date": "197502", "mkt": 11.0, "be_me_low": 13.0},
        {"date": "197501", "mkt": 1.0, "be_me_low": 3.0},
    ]
    rows = SugraFamaFrenchInternationalIndexReturnsFetcher.transform_data(query, data)
    assert [(str(r.date), r.mkt) for r in rows] == [
        ("1975-01-01", 1.0),
        ("1975-02-01", 11.0),
    ]


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


def test_currency_reference_rates_reshapes_one_wide_row():
    """The rates map becomes ONE wide row: date + EUR=1.0 + currency columns;
    unknown currency keys are dropped, not carried."""
    from openbb_core.provider.standard_models.currency_reference_rates import (
        CurrencyReferenceRatesQueryParams,
    )

    from openbb_sugra.models.currency_reference_rates import (
        SugraCurrencyReferenceRatesFetcher,
    )

    payload = {
        "base": "EUR", "date": "2026-06-25",
        "rates": {"USD": 1.08, "JPY": 168.5, "GBP": 0.862, "ZZZ": 9.9},
    }
    rows = SugraCurrencyReferenceRatesFetcher.transform_data(
        CurrencyReferenceRatesQueryParams(), payload
    )
    assert len(rows) == 1
    r = rows[0]
    assert str(r.date) == "2026-06-25"
    assert r.EUR == 1.0
    assert r.USD == 1.08 and r.JPY == 168.5 and r.GBP == 0.862
    # ZZZ is not a model field -> dropped, not present as an extra attribute.
    assert not hasattr(r, "ZZZ")


def test_currency_reference_rates_rejects_non_ecb_fallback():
    """A non-EUR base means the forex feed served a non-ECB fallback; refuse to
    emit a mislabelled reference-rate row."""
    from openbb_core.provider.standard_models.currency_reference_rates import (
        CurrencyReferenceRatesQueryParams,
    )
    from openbb_core.provider.utils.errors import EmptyDataError

    from openbb_sugra.models.currency_reference_rates import (
        SugraCurrencyReferenceRatesFetcher,
    )

    usd_base = {"base": "USD", "date": "2026-06-25", "rates": {"EUR": 0.92}}
    try:
        SugraCurrencyReferenceRatesFetcher.transform_data(
            CurrencyReferenceRatesQueryParams(), usd_base
        )
    except EmptyDataError as exc:
        assert "non-ECB fallback" in str(exc)
    else:
        raise AssertionError("a non-EUR base must raise EmptyDataError")

    # Empty rates and a missing date both raise (the two halves of the guard).
    for bad in (
        {"base": "EUR", "date": "2026-06-25", "rates": {}},
        {"base": "EUR", "date": None, "rates": {"USD": 1.08}},
    ):
        try:
            SugraCurrencyReferenceRatesFetcher.transform_data(
                CurrencyReferenceRatesQueryParams(), bad
            )
        except EmptyDataError:
            continue
        raise AssertionError(f"expected EmptyDataError for {bad}")


def test_yield_curve_validates_per_maturity_rows():
    """Per-maturity rows validate; maturity_years computes from year_N/month_N."""
    from openbb_sugra.models.yield_curve import (
        SugraYieldCurveFetcher,
        SugraYieldCurveQueryParams,
    )

    payload = {
        "date": "2026-06-24",
        "rates": [
            {"date": "2026-06-24", "maturity": "month_3", "rate": 0.0226},
            {"date": "2026-06-24", "maturity": "year_10", "rate": 0.0294},
        ],
    }
    rows = SugraYieldCurveFetcher.transform_data(
        SugraYieldCurveQueryParams(), payload
    )
    assert len(rows) == 2
    by_mat = {r.maturity: r for r in rows}
    assert by_mat["year_10"].rate == 0.0294
    assert by_mat["year_10"].maturity_years == 10.0
    assert by_mat["month_3"].maturity_years == pytest.approx(0.25)


def test_yield_curve_empty_raises():
    from openbb_core.provider.utils.errors import EmptyDataError

    from openbb_sugra.models.yield_curve import (
        SugraYieldCurveFetcher,
        SugraYieldCurveQueryParams,
    )

    try:
        SugraYieldCurveFetcher.transform_data(
            SugraYieldCurveQueryParams(), {"rates": []}
        )
    except EmptyDataError:
        return
    raise AssertionError("empty rates must raise EmptyDataError")


def test_balance_of_payments_coerces_period_and_validates():
    """Wide rows validate into the merged model; ECB period -> quarter/month-start date."""
    from datetime import date

    from openbb_sugra.models.balance_of_payments import (
        SugraBalanceOfPaymentsFetcher,
        SugraBalanceOfPaymentsQueryParams,
    )

    monthly = {
        "report_type": "main",
        "data": [
            {"period": "2024-03", "current_account": 39.88, "goods": 36.31,
             "errors_and_omissions": 1.2},
        ],
    }
    rows = SugraBalanceOfPaymentsFetcher.transform_data(
        SugraBalanceOfPaymentsQueryParams(report_type="main"), monthly
    )
    assert len(rows) == 1
    assert rows[0].period == date(2024, 3, 1)
    assert rows[0].current_account == 39.88

    quarterly = {
        "report_type": "country",
        "data": [{"period": "2024-Q2", "current_account_balance": -1.02}],
    }
    qrows = SugraBalanceOfPaymentsFetcher.transform_data(
        SugraBalanceOfPaymentsQueryParams(report_type="country", country="united_states"),
        quarterly,
    )
    assert qrows[0].period == date(2024, 4, 1)
    assert qrows[0].current_account_balance == -1.02


def test_balance_of_payments_empty_raises():
    from openbb_core.provider.utils.errors import EmptyDataError

    from openbb_sugra.models.balance_of_payments import (
        SugraBalanceOfPaymentsFetcher,
        SugraBalanceOfPaymentsQueryParams,
    )

    try:
        SugraBalanceOfPaymentsFetcher.transform_data(
            SugraBalanceOfPaymentsQueryParams(), {"data": []}
        )
    except EmptyDataError:
        return
    raise AssertionError("empty data must raise EmptyDataError")


def test_yield_curve_drops_bad_row_keeps_good():
    """A single malformed maturity is dropped, not fatal to the whole curve."""
    from openbb_sugra.models.yield_curve import (
        SugraYieldCurveFetcher,
        SugraYieldCurveQueryParams,
    )

    payload = {"rates": [
        {"date": "2026-06-24", "maturity": "year_10", "rate": 0.0294},
        {"date": "2026-06-24", "maturity": "year_5", "rate": "not-a-number"},
    ]}
    rows = SugraYieldCurveFetcher.transform_data(
        SugraYieldCurveQueryParams(), payload
    )
    assert len(rows) == 1 and rows[0].maturity == "year_10"


def test_balance_of_payments_period_bounds_and_drop():
    """_period_to_date rejects out-of-range months/quarters; an all-bad batch
    raises the distinct validation error, not a raw ValidationError."""
    from openbb_core.provider.utils.errors import EmptyDataError

    from openbb_sugra.models.balance_of_payments import (
        SugraBalanceOfPaymentsFetcher,
        SugraBalanceOfPaymentsQueryParams,
        _period_to_date,
    )

    assert _period_to_date("2024-03") == "2024-03-01"
    assert _period_to_date("2024-Q3") == "2024-07-01"
    assert _period_to_date("2024") == "2024-01-01"
    for bad in ("2024-13", "2024-00", "2024-Q5", "garbage", "g-03", ""):
        assert _period_to_date(bad) is None, bad

    # A row whose period cannot form a date is dropped (period None still
    # validates, so it survives) - use a hard validation failure instead.
    only_bad = {"data": [{"period": "2024-03", "current_account": "not-a-number"}]}
    try:
        SugraBalanceOfPaymentsFetcher.transform_data(
            SugraBalanceOfPaymentsQueryParams(), only_bad
        )
    except EmptyDataError as exc:
        assert "failed standard-model validation" in str(exc)
        return
    raise AssertionError("an all-invalid batch must raise EmptyDataError")
