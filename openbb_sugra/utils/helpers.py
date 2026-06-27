"""Shared HTTP helpers for the Sugra OpenBB provider.

All Sugra calls go through these helpers so the base URL, auth header, and
envelope handling live in one place. Heavy imports stay inside the functions to
keep ``import openbb`` time low.
"""

import contextlib
import logging
import re
from typing import Any

SUGRA_BASE_URL = "https://sugra.ai"

logger = logging.getLogger(__name__)

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


def kf_period_to_iso(raw: str) -> str:
    """Normalise a Ken French period token to an ISO date (YYYY-MM-DD).

    The Sugra Fama-French endpoints return the raw upstream period token:
    YYYYMMDD (daily) / YYYYMM (monthly) / YYYY (annual). Returns the input
    unchanged when it is not one of those widths.
    """
    raw = (raw or "").strip()
    if len(raw) == 8:
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    if len(raw) == 6:
        return f"{raw[:4]}-{raw[4:6]}-01"
    if len(raw) == 4:
        return f"{raw}-12-31"
    return raw


def fred_observations(payload: Any) -> list[dict]:
    """Return cleaned, date-ascending ``[{date, value}]`` rows from a FRED payload.

    The Sugra ``/api/v1/fred/series/{id}`` endpoint already coerces FRED's ``"."``
    gaps to ``None`` and casts values to float, so this drops null/empty
    observations, keeps the float value, and sorts ascending (the order OpenBB
    standard models present). Normalisation - percent vs fraction (``x-frontend_multiply``)
    - stays explicit in each fetcher; this only handles the shared plumbing.
    """
    observations = (payload or {}).get("observations") or []
    rows: list[dict] = []
    for obs in observations:
        if not isinstance(obs, dict) or obs.get("date") is None:
            continue
        value = obs.get("value")
        if isinstance(value, str):
            if value.strip() in {"", "."}:
                continue
            value = float(value)
        if value is None:
            continue
        rows.append({"date": obs["date"], "value": value})
    rows.sort(key=lambda r: r["date"])
    return rows


async def fred_series_payloads(
    api_key: str,
    series_ids: list[str],
    *,
    start_date: Any = None,
    end_date: Any = None,
    limit: int = 1000,
    base_url: str = SUGRA_BASE_URL,
) -> dict[str, dict]:
    """Fetch several FRED series concurrently; return ``{series_id: payload}``.

    Multi-field rate models (OBFR, ESTR, AMERIBOR, FOMC projections) are one
    standard model backed by a fixed set of FRED series. The single-series proxy
    is hit once per id in parallel and the unwrapped payloads are keyed by id for
    the caller to pivot or melt. A non-dict payload becomes an empty dict.
    """
    # pylint: disable=import-outside-toplevel
    import asyncio

    params: dict[str, Any] = {"limit": limit, "sort_order": "desc"}
    if start_date:
        params["observation_start"] = str(start_date)
    if end_date:
        params["observation_end"] = str(end_date)

    async def _one(series_id: str) -> tuple[str, dict]:
        response = await sugra_get(
            f"/api/v1/fred/series/{series_id}", api_key, params, base_url=base_url
        )
        payload = envelope_data(response)
        return series_id, payload if isinstance(payload, dict) else {}

    # One transient series failure must not sink the whole multi-field model:
    # gather all, log + drop any that raised, and let the caller decide whether
    # the surviving series are enough (a missing primary series -> EmptyDataError
    # downstream, optional fields just stay None).
    results = await asyncio.gather(
        *[_one(sid) for sid in series_ids], return_exceptions=True
    )
    payloads: dict[str, dict] = {}
    for series_id, result in zip(series_ids, results):
        if isinstance(result, Exception):
            logger.warning(
                "Sugra FRED series fetch failed for %s: %s", series_id, result
            )
            payloads[series_id] = {}
        elif isinstance(result, BaseException):
            # CancelledError / KeyboardInterrupt must propagate, not be dropped.
            raise result
        else:
            payloads[series_id] = result[1]
    return payloads
