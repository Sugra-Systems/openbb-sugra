"""Sugra Entity Screening — OpenBB Workspace custom backend (PoC).

A self-contained FastAPI backend that exposes Sugra's entity-screening
products (sanctions / PEP / KYB / wallet screening) as OpenBB Workspace
widgets. It is intentionally decoupled from the ``openbb_sugra`` provider
package — it talks to the Sugra HTTP API directly.

Run locally:
    uvicorn main:app --reload --port 8000

Then in OpenBB Workspace (pro.openbb.co): Apps → Connect backend →
http://localhost:8000 and the "Sugra Entity Screening" app appears.

Auth model (mirrors the marketplace trial → API-key flow):
    * ``entity_sources`` (coverage manifest) works with no key — the trust
      teaser that needs no authentication.
    * Every other widget calls a protected Sugra endpoint. Set
      ``SUGRA_API_KEY`` so the backend forwards it as ``x-api-key``; without
      it the upstream returns 401 and we surface a friendly message.

NOTE ON UPSTREAM SHAPES: the request bodies for the POST endpoints
(``/entity/screen``, ``/entity/resolve``, ``/entity/screen/batch``) and the
exact response field names are taken from the Sugra catalog summaries and
should be confirmed against the live API. Body construction is centralised
in ``sugra_call`` callers below so it is a one-line change if a key name
differs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

HERE = Path(__file__).parent.resolve()

SUGRA_API_BASE = os.getenv("SUGRA_API_BASE", "https://sugra.ai").rstrip("/")
SUGRA_API_KEY = os.getenv("SUGRA_API_KEY", "").strip()
HTTP_TIMEOUT = float(os.getenv("SUGRA_HTTP_TIMEOUT", "30"))

app = FastAPI(
    title="Sugra Entity Screening — OpenBB Workspace backend",
    description="Sanctions, PEP, KYB and wallet screening from the Sugra API.",
    version="0.1.0",
)

# OpenBB Workspace runs in the browser at pro.openbb.co and calls this backend
# directly, so it must be an allowed CORS origin. localhost covers local dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pro.openbb.co",
        "http://localhost:1420",
        "http://localhost:5050",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Sugra HTTP client
# --------------------------------------------------------------------------- #
async def sugra_call(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json_body: dict | None = None,
    require_key: bool = True,
) -> Any:
    """Call a Sugra endpoint and return the unwrapped ``data`` payload.

    ``path`` starts with ``/`` (e.g. ``/api/v1/entity/screen``). Raises an
    HTTPException with a friendly message on auth / upstream errors so the
    widget shows something useful instead of a stack trace.
    """
    if require_key and not SUGRA_API_KEY:
        raise HTTPException(
            status_code=401,
            detail=(
                "This widget needs a Sugra API key. Set SUGRA_API_KEY on the "
                "backend (get one at https://sugra.ai)."
            ),
        )

    headers = {"Accept": "application/json"}
    if SUGRA_API_KEY:
        headers["x-api-key"] = SUGRA_API_KEY

    url = f"{SUGRA_API_BASE}{path}"
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.request(
                method, url, params=params, json=json_body, headers=headers
            )
    except httpx.HTTPError as exc:  # network / timeout
        raise HTTPException(status_code=502, detail=f"Sugra API unreachable: {exc}")

    if resp.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="Sugra rejected the API key (401). Check SUGRA_API_KEY.",
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Sugra API error {resp.status_code}: {resp.text[:300]}",
        )

    payload = resp.json()
    # Unwrap the Sugra {data, meta} envelope when present.
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def as_rows(payload: Any) -> list[dict]:
    """Normalise an arbitrary Sugra payload into table rows.

    OpenBB table widgets want a JSON array of flat objects. We pass lists of
    dicts straight through, dig out the obvious list field from a dict, and
    fall back to wrapping a scalar/dict as a single row. Columns are
    auto-inferred by Workspace from the row keys (no columnsDefs needed).
    """
    if payload is None:
        return []
    if isinstance(payload, list):
        return [r if isinstance(r, dict) else {"value": r} for r in payload]
    if isinstance(payload, dict):
        for key in ("results", "hits", "matches", "items", "candidates", "rows"):
            inner = payload.get(key)
            if isinstance(inner, list):
                return [r if isinstance(r, dict) else {"value": r} for r in inner]
        return [payload]
    return [{"value": payload}]


# --------------------------------------------------------------------------- #
# Workspace plumbing endpoints
# --------------------------------------------------------------------------- #
@app.get("/")
def root() -> dict:
    return {"info": "Sugra Entity Screening backend for OpenBB Workspace"}


@app.get("/widgets.json")
def widgets() -> JSONResponse:
    return JSONResponse(content=json.loads((HERE / "widgets.json").read_text()))


@app.get("/apps.json")
def apps() -> JSONResponse:
    return JSONResponse(content=json.loads((HERE / "apps.json").read_text()))


# --------------------------------------------------------------------------- #
# Widget data endpoints
# --------------------------------------------------------------------------- #
@app.get("/entity_sources")
async def entity_sources() -> list[dict]:
    """Coverage manifest — sanctions/PEP source lists, freshness, regimes.

    No API key required: the trust teaser of the app.
    """
    data = await sugra_call("GET", "/api/v1/entity/sources", require_key=False)
    return as_rows(data)


@app.get("/entity_screen")
async def entity_screen(name: str = "") -> list[dict]:
    """Screen a single name against the sanctions/PEP corpus."""
    if not name:
        return []
    data = await sugra_call("POST", "/api/v1/entity/screen", json_body={"name": name})
    return as_rows(data)


@app.get("/entity_resolve")
async def entity_resolve(name: str = "") -> list[dict]:
    """Resolve a name to candidate corpus entities (disambiguation)."""
    if not name:
        return []
    data = await sugra_call("POST", "/api/v1/entity/resolve", json_body={"name": name})
    return as_rows(data)


@app.get("/entity_batch_screen")
async def entity_batch_screen(names: str = "") -> list[dict]:
    """Screen a comma-separated list of names in one batch call."""
    name_list = [n.strip() for n in names.split(",") if n.strip()]
    if not name_list:
        return []
    data = await sugra_call(
        "POST", "/api/v1/entity/screen/batch", json_body={"names": name_list}
    )
    return as_rows(data)


@app.get("/entity_wallet_screen")
async def entity_wallet_screen(address: str = "") -> list[dict]:
    """Screen a crypto wallet address against the sanctions corpus."""
    if not address:
        return []
    data = await sugra_call("GET", f"/api/v1/entity/wallet/{address}/screen")
    return as_rows(data)


@app.get("/entity_id_screen")
async def entity_id_screen(id_type: str = "passport", value: str = "") -> list[dict]:
    """Screen a document identifier (passport, national id, ...)."""
    if not value:
        return []
    data = await sugra_call("GET", f"/api/v1/entity/id/{id_type}/{value}/screen")
    return as_rows(data)


@app.get("/entity_kyb")
async def entity_kyb(anchor: str = "name", value: str = "") -> str:
    """Compose the full KYB envelope for an entity, rendered as markdown."""
    if not value:
        return "Enter an entity value to compose its KYB profile."
    data = await sugra_call("GET", f"/api/v1/entity/{anchor}/{value}")
    return "```json\n" + json.dumps(data, indent=2, default=str) + "\n```"


@app.get("/entity_adverse_media")
async def entity_adverse_media(anchor: str = "name", value: str = "") -> list[dict]:
    """Adverse-media slice of the KYB envelope for an entity."""
    if not value:
        return []
    data = await sugra_call("GET", f"/api/v1/entity/{anchor}/{value}/adverse-media")
    return as_rows(data)
