"""Sugra provider for the OpenBB Platform.

One Sugra API key spans many OpenBB data domains. This package registers the
``sugra`` provider via the ``openbb_provider_extension`` entry point so that an
``import openbb`` auto-discovers it. Every fetcher below has been live-verified
to return real data from the Sugra API and through the OpenBB ``obb.*`` layer.
"""

from openbb_core.provider.abstract.provider import Provider

from openbb_sugra.models.aggressive_small_caps import (
    SugraEquityAggressiveSmallCapsFetcher,
)
from openbb_sugra.models.ameribor import SugraAmeriborFetcher
from openbb_sugra.models.analyst_estimates import SugraAnalystEstimatesFetcher
from openbb_sugra.models.available_indices import SugraAvailableIndicesFetcher
from openbb_sugra.models.balance_of_payments import SugraBalanceOfPaymentsFetcher
from openbb_sugra.models.balance_sheet import SugraBalanceSheetFetcher
from openbb_sugra.models.bls_search import SugraBlsSearchFetcher
from openbb_sugra.models.bls_series import SugraBlsSeriesFetcher
from openbb_sugra.models.bond_indices import SugraBondIndicesFetcher
from openbb_sugra.models.calendar_dividend import SugraCalendarDividendFetcher
from openbb_sugra.models.calendar_earnings import SugraCalendarEarningsFetcher
from openbb_sugra.models.calendar_splits import SugraCalendarSplitsFetcher
from openbb_sugra.models.cash_flow import SugraCashFlowStatementFetcher
from openbb_sugra.models.commercial_paper import SugraCommercialPaperFetcher
from openbb_sugra.models.commodity_spot_prices import SugraCommoditySpotPricesFetcher
from openbb_sugra.models.company_filings import SugraCompanyFilingsFetcher
from openbb_sugra.models.company_news import SugraCompanyNewsFetcher
from openbb_sugra.models.composite_leading_indicator import (
    SugraCompositeLeadingIndicatorFetcher,
)
from openbb_sugra.models.congress_amendment_info import SugraCongressAmendmentInfoFetcher
from openbb_sugra.models.congress_amendments import SugraCongressAmendmentsFetcher
from openbb_sugra.models.congress_bill_info import SugraCongressBillInfoFetcher
from openbb_sugra.models.congress_bills import SugraCongressBillsFetcher
from openbb_sugra.models.congress_committee_documents import (
    SugraCongressCommitteeDocumentsFetcher,
)
from openbb_sugra.models.congress_committee_info import (
    SugraCongressCommitteeInfoFetcher,
)
from openbb_sugra.models.consumer_price_index import SugraConsumerPriceIndexFetcher
from openbb_sugra.models.cot import SugraCOTFetcher
from openbb_sugra.models.cot_search import SugraCotSearchFetcher
from openbb_sugra.models.country_interest_rates import (
    SugraCountryInterestRatesFetcher,
)
from openbb_sugra.models.crypto_historical import SugraCryptoHistoricalFetcher
from openbb_sugra.models.crypto_search import SugraCryptoSearchFetcher
from openbb_sugra.models.currency_historical import SugraCurrencyHistoricalFetcher
from openbb_sugra.models.currency_pairs import SugraCurrencyPairsFetcher
from openbb_sugra.models.currency_reference_rates import (
    SugraCurrencyReferenceRatesFetcher,
)
from openbb_sugra.models.currency_snapshots import SugraCurrencySnapshotsFetcher
from openbb_sugra.models.discount_window_primary_credit_rate import (
    SugraDiscountWindowPrimaryCreditRateFetcher,
)
from openbb_sugra.models.ecb_interest_rates import SugraECBInterestRatesFetcher
from openbb_sugra.models.equity_active import SugraEquityActiveFetcher
from openbb_sugra.models.equity_gainers import SugraEquityGainersFetcher
from openbb_sugra.models.equity_historical import SugraEquityHistoricalFetcher
from openbb_sugra.models.equity_info import SugraEquityInfoFetcher
from openbb_sugra.models.equity_losers import SugraEquityLosersFetcher
from openbb_sugra.models.equity_ownership import SugraEquityOwnershipFetcher
from openbb_sugra.models.equity_quote import SugraEquityQuoteFetcher
from openbb_sugra.models.equity_screener import SugraEquityScreenerFetcher
from openbb_sugra.models.equity_search import SugraEquitySearchFetcher
from openbb_sugra.models.etf_historical import SugraEtfHistoricalFetcher
from openbb_sugra.models.etf_holdings import SugraEtfHoldingsFetcher
from openbb_sugra.models.etf_info import SugraEtfInfoFetcher
from openbb_sugra.models.etf_price_performance import SugraEtfPricePerformanceFetcher
from openbb_sugra.models.etf_search import SugraEtfSearchFetcher
from openbb_sugra.models.euro_short_term_rate import SugraEuroShortTermRateFetcher
from openbb_sugra.models.famafrench_breakpoints import (
    SugraFamaFrenchBreakpointFetcher,
)
from openbb_sugra.models.famafrench_country_portfolio_returns import (
    SugraFamaFrenchCountryPortfolioReturnsFetcher,
)
from openbb_sugra.models.famafrench_factors import SugraFamaFrenchFactorsFetcher
from openbb_sugra.models.famafrench_international_index_returns import (
    SugraFamaFrenchInternationalIndexReturnsFetcher,
)
from openbb_sugra.models.famafrench_regional_portfolio_returns import (
    SugraFamaFrenchRegionalPortfolioReturnsFetcher,
)
from openbb_sugra.models.famafrench_us_portfolio_returns import (
    SugraFamaFrenchUSPortfolioReturnsFetcher,
)
from openbb_sugra.models.fed_projections import SugraFedProjectionsFetcher
from openbb_sugra.models.federal_funds_rate import SugraFederalFundsRateFetcher
from openbb_sugra.models.financial_ratios import SugraFinancialRatiosFetcher
from openbb_sugra.models.form_13FHR import SugraForm13FHRFetcher
from openbb_sugra.models.forward_ebitda_estimates import (
    SugraForwardEbitdaEstimatesFetcher,
)
from openbb_sugra.models.forward_eps_estimates import SugraForwardEpsEstimatesFetcher
from openbb_sugra.models.forward_sales_estimates import (
    SugraForwardSalesEstimatesFetcher,
)
from openbb_sugra.models.fred_search import SugraFredSearchFetcher
from openbb_sugra.models.fred_series import SugraFredSeriesFetcher
from openbb_sugra.models.gdp_forecast import SugraGdpForecastFetcher
from openbb_sugra.models.gdp_nominal import SugraGdpNominalFetcher
from openbb_sugra.models.gdp_real import SugraGdpRealFetcher
from openbb_sugra.models.growth_tech_equities import SugraGrowthTechEquitiesFetcher
from openbb_sugra.models.historical_dividends import SugraHistoricalDividendsFetcher
from openbb_sugra.models.historical_splits import SugraHistoricalSplitsFetcher
from openbb_sugra.models.house_price_index import SugraHousePriceIndexFetcher
from openbb_sugra.models.income_statement import SugraIncomeStatementFetcher
from openbb_sugra.models.index_constituents import SugraIndexConstituentsFetcher
from openbb_sugra.models.index_historical import SugraIndexHistoricalFetcher
from openbb_sugra.models.insider_trading import SugraInsiderTradingFetcher
from openbb_sugra.models.institutional_ownership import (
    SugraInstitutionalOwnershipFetcher,
)
from openbb_sugra.models.iorb_rates import SugraIORBFetcher
from openbb_sugra.models.key_metrics import SugraKeyMetricsFetcher
from openbb_sugra.models.manufacturing_outlook_ny import (
    SugraManufacturingOutlookNYFetcher,
)
from openbb_sugra.models.manufacturing_outlook_texas import (
    SugraManufacturingOutlookTexasFetcher,
)
from openbb_sugra.models.maritime_chokepoint_info import (
    SugraMaritimeChokePointInfoFetcher,
)
from openbb_sugra.models.maritime_chokepoint_volume import (
    SugraMaritimeChokePointVolumeFetcher,
)
from openbb_sugra.models.market_snapshots import SugraMarketSnapshotsFetcher
from openbb_sugra.models.money_measures import SugraMoneyMeasuresFetcher
from openbb_sugra.models.mortgage_indices import SugraMortgageIndicesFetcher
from openbb_sugra.models.non_farm_payrolls import SugraNonFarmPayrollsFetcher
from openbb_sugra.models.options_chains import SugraOptionsChainsFetcher
from openbb_sugra.models.overnight_bank_funding_rate import (
    SugraOvernightBankFundingRateFetcher,
)
from openbb_sugra.models.personal_consumption_expenditures import (
    SugraPersonalConsumptionExpendituresFetcher,
)
from openbb_sugra.models.petroleum_status_report import (
    SugraPetroleumStatusReportFetcher,
)
from openbb_sugra.models.port_info import SugraPortInfoFetcher
from openbb_sugra.models.port_volume import SugraPortVolumeFetcher
from openbb_sugra.models.price_performance import SugraPricePerformanceFetcher
from openbb_sugra.models.price_target_consensus import SugraPriceTargetConsensusFetcher
from openbb_sugra.models.retail_prices import SugraRetailPricesFetcher
from openbb_sugra.models.selected_treasury_bill import SugraSelectedTreasuryBillFetcher
from openbb_sugra.models.selected_treasury_constant_maturity import (
    SugraSelectedTreasuryConstantMaturityFetcher,
)
from openbb_sugra.models.senior_loan_officer_survey import (
    SugraSeniorLoanOfficerSurveyFetcher,
)
from openbb_sugra.models.share_price_index import SugraSharePriceIndexFetcher
from openbb_sugra.models.share_statistics import SugraShareStatisticsFetcher
from openbb_sugra.models.short_term_energy_outlook import (
    SugraShortTermEnergyOutlookFetcher,
)
from openbb_sugra.models.sofr import SugraSOFRFetcher
from openbb_sugra.models.sonia_rates import SugraSONIAFetcher
from openbb_sugra.models.spot_rate import SugraSpotRateFetcher
from openbb_sugra.models.survey_of_economic_conditions_chicago import (
    SugraSurveyOfEconomicConditionsChicagoFetcher,
)
from openbb_sugra.models.trailing_dividend_yield import SugraTrailingDivYieldFetcher
from openbb_sugra.models.treasury_auctions import SugraUSTreasuryAuctionsFetcher
from openbb_sugra.models.treasury_constant_maturity import (
    SugraTreasuryConstantMaturityFetcher,
)
from openbb_sugra.models.treasury_rates import SugraTreasuryRatesFetcher
from openbb_sugra.models.undervalued_growth_equities import (
    SugraUndervaluedGrowthEquitiesFetcher,
)
from openbb_sugra.models.undervalued_large_caps import SugraUndervaluedLargeCapsFetcher
from openbb_sugra.models.unemployment import SugraUnemploymentFetcher
from openbb_sugra.models.university_of_michigan import (
    SugraUniversityOfMichiganFetcher,
)
from openbb_sugra.models.world_news import SugraWorldNewsFetcher
from openbb_sugra.models.yield_curve import SugraYieldCurveFetcher

sugra_provider = Provider(
    name="sugra",
    website="https://sugra.ai",
    description=(
        "Sugra is intelligence infrastructure - a single API spanning markets, "
        "fundamentals, estimates, options, crypto, currencies, news, macro and "
        "rates, treasuries, ETFs, indices, and maritime data. One Sugra key "
        "fulfils data across many OpenBB domains, so you wire in once instead "
        "of stitching together many separate sources."
    ),
    credentials=["api_key"],
    fetcher_dict={
        "Ameribor": SugraAmeriborFetcher,
        "AnalystEstimates": SugraAnalystEstimatesFetcher,
        "AvailableIndices": SugraAvailableIndicesFetcher,
        "BalanceOfPayments": SugraBalanceOfPaymentsFetcher,
        "BalanceSheet": SugraBalanceSheetFetcher,
        "BlsSearch": SugraBlsSearchFetcher,
        "BlsSeries": SugraBlsSeriesFetcher,
        "BondIndices": SugraBondIndicesFetcher,
        "COT": SugraCOTFetcher,
        "COTSearch": SugraCotSearchFetcher,
        "CalendarDividend": SugraCalendarDividendFetcher,
        "CalendarEarnings": SugraCalendarEarningsFetcher,
        "CalendarSplits": SugraCalendarSplitsFetcher,
        "CashFlowStatement": SugraCashFlowStatementFetcher,
        "CommercialPaper": SugraCommercialPaperFetcher,
        "CommoditySpotPrices": SugraCommoditySpotPricesFetcher,
        "CompanyFilings": SugraCompanyFilingsFetcher,
        "CompanyNews": SugraCompanyNewsFetcher,
        "CompositeLeadingIndicator": SugraCompositeLeadingIndicatorFetcher,
        "CongressAmendmentInfo": SugraCongressAmendmentInfoFetcher,
        "CongressAmendments": SugraCongressAmendmentsFetcher,
        "CongressBillInfo": SugraCongressBillInfoFetcher,
        "CongressBills": SugraCongressBillsFetcher,
        "CongressCommitteeDocuments": SugraCongressCommitteeDocumentsFetcher,
        "CongressCommitteeInfo": SugraCongressCommitteeInfoFetcher,
        "ConsumerPriceIndex": SugraConsumerPriceIndexFetcher,
        "CountryInterestRates": SugraCountryInterestRatesFetcher,
        "CryptoHistorical": SugraCryptoHistoricalFetcher,
        "CryptoSearch": SugraCryptoSearchFetcher,
        "CurrencyHistorical": SugraCurrencyHistoricalFetcher,
        "CurrencyPairs": SugraCurrencyPairsFetcher,
        "CurrencyReferenceRates": SugraCurrencyReferenceRatesFetcher,
        "CurrencySnapshots": SugraCurrencySnapshotsFetcher,
        "DiscountWindowPrimaryCreditRate": SugraDiscountWindowPrimaryCreditRateFetcher,
        "EquityActive": SugraEquityActiveFetcher,
        "EquityAggressiveSmallCaps": SugraEquityAggressiveSmallCapsFetcher,
        "EquityGainers": SugraEquityGainersFetcher,
        "EquityHistorical": SugraEquityHistoricalFetcher,
        "EquityInfo": SugraEquityInfoFetcher,
        "EquityLosers": SugraEquityLosersFetcher,
        "EquityOwnership": SugraEquityOwnershipFetcher,
        "EquityQuote": SugraEquityQuoteFetcher,
        "EquityScreener": SugraEquityScreenerFetcher,
        "EquitySearch": SugraEquitySearchFetcher,
        "EquityUndervaluedGrowth": SugraUndervaluedGrowthEquitiesFetcher,
        "EquityUndervaluedLargeCaps": SugraUndervaluedLargeCapsFetcher,
        "EtfHistorical": SugraEtfHistoricalFetcher,
        "EtfHoldings": SugraEtfHoldingsFetcher,
        "EtfInfo": SugraEtfInfoFetcher,
        "EtfPricePerformance": SugraEtfPricePerformanceFetcher,
        "EtfSearch": SugraEtfSearchFetcher,
        "EuropeanCentralBankInterestRates": SugraECBInterestRatesFetcher,
        "EuroShortTermRate": SugraEuroShortTermRateFetcher,
        "FamaFrenchBreakpoints": SugraFamaFrenchBreakpointFetcher,
        "FamaFrenchCountryPortfolioReturns": SugraFamaFrenchCountryPortfolioReturnsFetcher,
        "FamaFrenchFactors": SugraFamaFrenchFactorsFetcher,
        "FamaFrenchInternationalIndexReturns": SugraFamaFrenchInternationalIndexReturnsFetcher,
        "FamaFrenchRegionalPortfolioReturns": SugraFamaFrenchRegionalPortfolioReturnsFetcher,
        "FamaFrenchUSPortfolioReturns": SugraFamaFrenchUSPortfolioReturnsFetcher,
        "FederalFundsRate": SugraFederalFundsRateFetcher,
        "FinancialRatios": SugraFinancialRatiosFetcher,
        "Form13FHR": SugraForm13FHRFetcher,
        "ForwardEbitdaEstimates": SugraForwardEbitdaEstimatesFetcher,
        "ForwardEpsEstimates": SugraForwardEpsEstimatesFetcher,
        "ForwardSalesEstimates": SugraForwardSalesEstimatesFetcher,
        "FredSearch": SugraFredSearchFetcher,
        "FredSeries": SugraFredSeriesFetcher,
        "GdpForecast": SugraGdpForecastFetcher,
        "GdpNominal": SugraGdpNominalFetcher,
        "GdpReal": SugraGdpRealFetcher,
        "GrowthTechEquities": SugraGrowthTechEquitiesFetcher,
        "HistoricalDividends": SugraHistoricalDividendsFetcher,
        "HistoricalSplits": SugraHistoricalSplitsFetcher,
        "HousePriceIndex": SugraHousePriceIndexFetcher,
        "IncomeStatement": SugraIncomeStatementFetcher,
        "IndexConstituents": SugraIndexConstituentsFetcher,
        "IndexHistorical": SugraIndexHistoricalFetcher,
        "InsiderTrading": SugraInsiderTradingFetcher,
        "IORB": SugraIORBFetcher,
        "InstitutionalOwnership": SugraInstitutionalOwnershipFetcher,
        "KeyMetrics": SugraKeyMetricsFetcher,
        "MaritimeChokePointInfo": SugraMaritimeChokePointInfoFetcher,
        "MaritimeChokePointVolume": SugraMaritimeChokePointVolumeFetcher,
        "ManufacturingOutlookNY": SugraManufacturingOutlookNYFetcher,
        "ManufacturingOutlookTexas": SugraManufacturingOutlookTexasFetcher,
        "MarketSnapshots": SugraMarketSnapshotsFetcher,
        "MoneyMeasures": SugraMoneyMeasuresFetcher,
        "MortgageIndices": SugraMortgageIndicesFetcher,
        "NonFarmPayrolls": SugraNonFarmPayrollsFetcher,
        "OptionsChains": SugraOptionsChainsFetcher,
        "OvernightBankFundingRate": SugraOvernightBankFundingRateFetcher,
        "PROJECTIONS": SugraFedProjectionsFetcher,
        "PersonalConsumptionExpenditures": SugraPersonalConsumptionExpendituresFetcher,
        "PetroleumStatusReport": SugraPetroleumStatusReportFetcher,
        "PortInfo": SugraPortInfoFetcher,
        "PortVolume": SugraPortVolumeFetcher,
        "PricePerformance": SugraPricePerformanceFetcher,
        "PriceTargetConsensus": SugraPriceTargetConsensusFetcher,
        "SOFR": SugraSOFRFetcher,
        "SONIA": SugraSONIAFetcher,
        "SelectedTreasuryBill": SugraSelectedTreasuryBillFetcher,
        "SpotRate": SugraSpotRateFetcher,
        "SelectedTreasuryConstantMaturity": SugraSelectedTreasuryConstantMaturityFetcher,
        "SeniorLoanOfficerSurvey": SugraSeniorLoanOfficerSurveyFetcher,
        "RetailPrices": SugraRetailPricesFetcher,
        "SharePriceIndex": SugraSharePriceIndexFetcher,
        "ShareStatistics": SugraShareStatisticsFetcher,
        "ShortTermEnergyOutlook": SugraShortTermEnergyOutlookFetcher,
        "SurveyOfEconomicConditionsChicago": (
            SugraSurveyOfEconomicConditionsChicagoFetcher
        ),
        "TrailingDividendYield": SugraTrailingDivYieldFetcher,
        "TreasuryAuctions": SugraUSTreasuryAuctionsFetcher,
        "TreasuryConstantMaturity": SugraTreasuryConstantMaturityFetcher,
        "TreasuryRates": SugraTreasuryRatesFetcher,
        "Unemployment": SugraUnemploymentFetcher,
        "UniversityOfMichigan": SugraUniversityOfMichiganFetcher,
        "WorldNews": SugraWorldNewsFetcher,
        "YieldCurve": SugraYieldCurveFetcher,
    },
    repr_name="Sugra",
    instructions=(
        "Get a Sugra API key at https://sugra.ai. Set it as the environment "
        "variable OPENBB_SUGRA_API_KEY, or as credentials.sugra_api_key in your "
        "OpenBB user settings. The key is sent as the x-api-key request header."
    ),
)
