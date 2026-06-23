"""Shared HTTP helpers for the Sugra OpenBB provider.

All Sugra calls go through these helpers so the base URL, auth header, and
envelope handling live in one place. Heavy imports stay inside the functions to
keep ``import openbb`` time low.
"""

import contextlib
import re
from typing import Any

SUGRA_BASE_URL = "https://sugra.ai"

_CAMEL_RE = re.compile(r"(?<!^)(?=[A-Z])")


def to_snake(name: str) -> str:
    """Convert an upstream PascalCase concept name to snake_case."""
    return _CAMEL_RE.sub("_", name).lower()


def pivot_wide_matrix(payload: Any) -> list[dict]:
    """Pivot a Sugra wide statement matrix into one dict per period.

    Upstream shape: ``{"periods": [...], "data": {Concept: {period: value}}}``.
    Returns rows keyed by ``period_ending`` plus snake_cased concept fields,
    newest period first (the order returned by the API).
    """
    if not isinstance(payload, dict):
        return []
    periods = payload.get("periods") or []
    matrix = payload.get("data") or {}
    if not periods or not isinstance(matrix, dict):
        return []
    rows: list[dict] = []
    for period in periods:
        row: dict[str, Any] = {"period_ending": period}
        with contextlib.suppress(ValueError, TypeError):
            row["fiscal_year"] = int(str(period)[:4])
        for concept, by_period in matrix.items():
            if isinstance(by_period, dict) and period in by_period:
                row[to_snake(concept)] = by_period[period]
        rows.append(row)
    return rows


def get_api_key(credentials: dict | None) -> str:
    """Return the Sugra API key from OpenBB credentials, or raise."""
    # pylint: disable=import-outside-toplevel
    api_key = (credentials or {}).get("sugra_api_key")
    if not api_key:
        from openbb_core.provider.utils.errors import UnauthorizedError

        raise UnauthorizedError(
            "Missing Sugra API key. Set OPENBB_SUGRA_API_KEY or "
            "credentials.sugra_api_key. Get a key at https://sugra.ai."
        )
    return api_key


async def sugra_get(
    path: str,
    api_key: str,
    params: dict | None = None,
    base_url: str = SUGRA_BASE_URL,
) -> Any:
    """GET a Sugra endpoint and return the parsed JSON body.

    `path` starts with `/` (e.g. `/api/v2/quotes/AAPL/historical`).
    """
    # pylint: disable=import-outside-toplevel
    from openbb_core.provider.utils.helpers import amake_request, get_querystring

    query = get_querystring(params or {}, [])
    url = f"{base_url}{path}" + (f"?{query}" if query else "")
    headers = {"x-api-key": api_key, "Accept": "application/json"}
    # 30s allows for cold-cache responses on heavier endpoints; the default is 10s.
    return await amake_request(url, method="GET", headers=headers, timeout=30)


def envelope_data(response: Any) -> Any:
    """Unwrap the Sugra `{data, meta}` envelope and return `data`.

    Returns the response unchanged if it is not a dict with a `data` key.
    """
    if isinstance(response, dict) and "data" in response:
        return response["data"]
    return response
