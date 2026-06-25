# openbb-sugra coverage

One Sugra API key fulfils 80 OpenBB standard data models across 13 command groups. Install one provider, set one credential, and pull all of the below - instead of wiring many separate provider keys.

| OpenBB command group | What it covers | Models |
|---|---|---|
| equity (36) | Equities, fundamentals, estimates, ownership, calendars, discovery | obb.equity.calendar.dividend, obb.equity.calendar.earnings, obb.equity.calendar.splits, obb.equity.discovery.active, obb.equity.discovery.aggressive_small_caps, obb.equity.discovery.gainers, obb.equity.discovery.growth_tech, obb.equity.discovery.losers, obb.equity.discovery.undervalued_growth, obb.equity.discovery.undervalued_large_caps, obb.equity.estimates.consensus, obb.equity.estimates.forward_ebitda, obb.equity.estimates.forward_eps, obb.equity.estimates.forward_sales, obb.equity.estimates.historical, obb.equity.fundamental.balance, obb.equity.fundamental.cash, obb.equity.fundamental.dividends, obb.equity.fundamental.filings, obb.equity.fundamental.historical_splits, obb.equity.fundamental.income, obb.equity.fundamental.metrics, obb.equity.fundamental.ratios, obb.equity.fundamental.trailing_dividend_yield, obb.equity.market_snapshots, obb.equity.ownership.form_13f, obb.equity.ownership.insider_trading, obb.equity.ownership.institutional, obb.equity.ownership.major_holders, obb.equity.ownership.share_statistics, obb.equity.price.historical, obb.equity.price.performance, obb.equity.price.quote, obb.equity.profile, obb.equity.screener, obb.equity.search |
| economy (15) | Macro, GDP, inflation, employment, money, shipping/ports | obb.economy.cpi, obb.economy.fred_search, obb.economy.fred_series, obb.economy.gdp.nominal, obb.economy.gdp.real, obb.economy.money_measures, obb.economy.pce, obb.economy.shipping.chokepoint_info, obb.economy.shipping.chokepoint_volume, obb.economy.shipping.port_info, obb.economy.shipping.port_volume, obb.economy.survey.bls_search, obb.economy.survey.bls_series, obb.economy.survey.nonfarm_payrolls, obb.economy.unemployment |
| famafrench (1) | Fama-French academic factor returns | obb.famafrench.factors |
| etf (5) | ETFs | obb.etf.historical, obb.etf.holdings, obb.etf.info, obb.etf.price_performance, obb.etf.search |
| currency (4) | Forex | obb.currency.price.historical, obb.currency.reference_rates, obb.currency.search, obb.currency.snapshots |
| fixedincome (4) | Rates and fixed income | obb.fixedincome.government.treasury_auctions, obb.fixedincome.rate.effr, obb.fixedincome.rate.sofr, obb.fixedincome.rate.sonia |
| index (3) | Indices | obb.index.available, obb.index.constituents, obb.index.price.historical |
| cftc (2) | CFTC Commitment of Traders | obb.cftc.cot, obb.cftc.cot_search |
| commodity (3) | Commodities and energy | obb.commodity.petroleum_status_report, obb.commodity.price.spot, obb.commodity.short_term_energy_outlook |
| crypto (2) | Crypto | obb.crypto.price.historical, obb.crypto.search |
| news (2) | News | obb.news.company, obb.news.world |
| uscongress (2) | US Congress bills and amendments | obb.uscongress.amendments, obb.uscongress.bills |
| derivatives (1) | Options | obb.derivatives.options.chains |

Every model above is live-verified against the Sugra API and through the OpenBB obb.* layer. OpenBB models that Sugra does not yet cover are tracked separately and added as the underlying data lands.
