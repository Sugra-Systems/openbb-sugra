"""Shared helpers for Sugra predefined-screener (equity performance) models.

The Sugra `/api/v2/market/screener/{scr_id}` endpoint backs OpenBB's equity
discovery models (active, gainers, losers, undervalued growth/large-caps).
Each maps onto the EquityPerformance standard shape, so the fetch + field
mapping lives here once and the per-model files stay thin.
"""


def map_record(record: dict) -> dict:
    """Map one Sugra screener record onto EquityPerformance fields."""
    return {
        "symbol": record.get("symbol"),
        "name": record.get("name"),
        "price": record.get("price"),
        "change": record.get("change"),
        # Sugra's predefined-screener change_pct is a WHOLE percent (e.g. 49.79 =
        # 49.79%), but EquityPerformance.percent_change expects a normalized
        # fraction (the field carries x-frontend_multiply 100), so divide by 100 -
        # matching FMP's equity screeners (openbb_fmp equity_gainers _normalize_percent).
        "percent_change": (
            record.get("change_pct") / 100.0
            if isinstance(record.get("change_pct"), (int, float))
            else None
        ),
        "volume": record.get("volume"),
    }


async def fetch_predefined(
    scr_id: str,
    credentials: dict[str, str] | None,
    count: int = 25,
) -> list[dict]:
    """Fetch and unwrap predefined-screener records from the Sugra API."""
    # pylint: disable=import-outside-toplevel
    from openbb_sugra.utils.helpers import envelope_data, get_api_key, sugra_get

    api_key = get_api_key(credentials)
    response = await sugra_get(f"/api/v2/market/screener/{scr_id}", api_key, {"count": count})
    payload = envelope_data(response)
    records = payload.get("records", []) if isinstance(payload, dict) else []
    out: list[dict] = []
    for r in records:
        if not isinstance(r, dict) or not r.get("symbol"):
            continue
        mapped = map_record(r)
        # EquityPerformance requires price/change/percent_change to be present.
        if mapped["price"] is None or mapped["change"] is None or mapped["percent_change"] is None:
            continue
        out.append(mapped)
    return out


def sort_records(records: list[dict], sort: str) -> list[dict]:
    """Sort by percent_change per the standard `sort` query param."""
    reverse = sort != "asc"
    return sorted(records, key=lambda r: r.get("percent_change") or 0.0, reverse=reverse)
