<div align="center">

<img src="https://raw.githubusercontent.com/Sugra-Systems/openbb-sugra/main/assets/coverage.png" alt="Sugra for OpenBB - 88 OpenBB data models from one Sugra key" width="960">

# openbb-sugra

**Sugra data provider extension for the [OpenBB Platform](https://github.com/OpenBB-finance/OpenBB).**

[![PyPI](https://img.shields.io/pypi/v/openbb-sugra?color=00AAFF&label=PyPI&cacheSeconds=3600)](https://pypi.org/project/openbb-sugra/)
[![Python](https://img.shields.io/badge/python-3.10--3.12-00AAFF)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-00AAFF)](LICENSE)
[![OpenBB](https://img.shields.io/badge/OpenBB-provider-00AAFF)](https://docs.openbb.co/)

One Sugra API key. 88 OpenBB data models. One provider.

</div>

---

**One Sugra API key. 88 OpenBB data models. One provider.**

Wire in one credential and pull equities and fundamentals, estimates, ownership, calendars, options, crypto, currencies, news, macro and rates, treasuries, ETFs and indices, commodities, and maritime data - the breadth that otherwise needs many separate provider keys. Every model is live-verified against the Sugra API and through the OpenBB `obb.*` layer.

## 1. Install

```bash
pip install openbb-sugra
```

The provider auto-registers with OpenBB through the `openbb_provider_extension` entry point. After install, `import openbb` rebuilds the static package and the `sugra` provider becomes available.

## 2. Get a key

Get a Sugra API key at [sugra.ai](https://sugra.ai), then set it once:

```bash
export OPENBB_SUGRA_API_KEY="your_key"
```

or add it to `~/.openbb_platform/user_settings.json`:

```json
{ "credentials": { "sugra_api_key": "your_key" } }
```

The key is sent as the `x-api-key` request header. Volume-only pricing, commercial use permitted on every tier.

## 3. Use

```python
from openbb import obb

obb.equity.price.historical("AAPL", provider="sugra")
obb.economy.fred_series("GDP", provider="sugra")
obb.crypto.price.historical("BITCOIN", provider="sugra")
```

## 4. Coverage

A single Sugra key fulfils 88 OpenBB standard data models across thirteen command groups - equity, economy, Fama-French, ETF, currency, fixed income, index, CFTC, commodity, crypto, news, US Congress, and derivatives. The full matrix is generated from the shipped fetchers - see [`COVERAGE.md`](https://github.com/Sugra-Systems/openbb-sugra/blob/main/COVERAGE.md).

## 5. License

AGPL-3.0-only. This package links the AGPL-3.0 `openbb-core` library. The Sugra API itself is a separate hosted service reached over HTTPS. See [`LICENSE`](https://github.com/Sugra-Systems/openbb-sugra/blob/main/LICENSE).

---

<div align="center">
Sugra <em>Systems, Inc.</em> &nbsp;&middot;&nbsp; <a href="https://sugra.ai">sugra.ai</a>
</div>
