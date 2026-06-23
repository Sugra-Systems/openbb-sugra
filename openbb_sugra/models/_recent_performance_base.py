"""Shared helpers for Sugra recent-performance (price performance) models.

The Sugra ``/api/v2/quotes/{symbol}/recent-performance`` endpoint backs both
OpenBB ``PricePerformance`` (equity) and ``EtfPricePerformance`` (ETF). Both map
onto the RecentPerformanceData standard shape, so the fetch and the
percent-to-fraction normalization live here once.
"""

# RecentPerformanceData stores normalized decimal fractions (its fields carry
# ``x-frontend_multiply: 100``); the Sugra endpoint returns whole percents
# (e.g. ``1.1279`` == 1.1279%), so every trailing return is divided by 100.
RETURN_FIELDS = (
    "one_day",
    "wtd",
    "one_week",
    "mtd",
    "one_month",
    "qtd",
    "three_month",
    "six_month",
    "ytd",
    "one_year",
    "two_year",
    "three_year",
    "four_year",
    "five_year",
    "ten_year",
    "max",
)


async def fetch_recent_performance(
    symbols: str,
    credentials: dict[str, str] | None,
) -> list[dict]:
    """Fetch and percent-normalize recent-performance rows for one or more symbols.

    ``symbols`` may be a single ticker or a comma-separated list. Each trailing
    return is divided by 100 to match the RecentPerformanceData fraction shape.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

    api_key = get_api_key(credentials)
    out: list[dict] = []
    for symbol in [s.strip().upper() for s in str(symbols).split(",") if s.strip()]:
        response = await sugra_get(f"/api/v2/quotes/{symbol}/recent-performance", api_key)
        payload = envelope_data(response)
        if not isinstance(payload, dict):
            continue
        row: dict = {"symbol": payload.get("symbol") or symbol}
        for field in RETURN_FIELDS:
            value = payload.get(field)
            row[field] = value / 100.0 if isinstance(value, (int, float)) else None
        out.append(row)
    return out
