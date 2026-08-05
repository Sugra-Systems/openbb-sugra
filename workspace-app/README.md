# Sugra Entity Screening — OpenBB Workspace app (PoC)

A standalone [OpenBB Workspace](https://pro.openbb.co) custom backend that
surfaces **Sugra Entity** — sanctions / PEP / KYB / crypto-wallet screening —
as interactive, Copilot-queryable widgets. This is the candidate first listing
for the [OpenBB App Marketplace](https://openbb.co/blog/introducing-the-openbb-app-marketplace/).

It is **decoupled from the `openbb-sugra` provider package** in this repo: it
talks to the Sugra HTTP API (`https://sugra.ai`) directly and can be lifted
into its own repository unchanged.

## Why Entity first

Every early marketplace partner ships market/alt data; none ship compliance
screening. Leading with Sugra Entity opens a new category instead of competing
on commodity OHLC/macro feeds. The trial → API-key access model maps cleanly:
the coverage widget needs no key, everything else unlocks with a Sugra key.

## Widgets

| Widget | Sugra endpoint | Needs key |
| --- | --- | --- |
| Sanctions & PEP Coverage | `GET /api/v1/entity/sources` | no |
| Name Screening | `POST /api/v1/entity/screen` | yes |
| Entity Resolution | `POST /api/v1/entity/resolve` | yes |
| Batch Screening | `POST /api/v1/entity/screen/batch` | yes |
| Wallet Screening | `GET /api/v1/entity/wallet/{address}/screen` | yes |
| Document ID Screening | `GET /api/v1/entity/id/{id_type}/{value}/screen` | yes |
| KYB Profile | `GET /api/v1/entity/{anchor}/{value}` | yes |
| Adverse Media | `GET /api/v1/entity/{anchor}/{value}/adverse-media` | yes |

The app (`apps.json`) lays these out across two tabs: **Screening** and
**KYB Profile**.

## Run locally

```bash
cd workspace-app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set SUGRA_API_KEY
export $(grep -v '^#' .env | xargs)
uvicorn main:app --reload --port 8000
```

Sanity check:

```bash
curl localhost:8000/widgets.json
curl localhost:8000/entity_sources          # works without a key
```

## Or with Docker

```bash
docker build -t sugra-entity-app .
docker run -p 8000:8000 -e SUGRA_API_KEY=your_key sugra-entity-app
```

## Connect to OpenBB Workspace

1. Open <https://pro.openbb.co> → **Apps** → **Connect backend** (a.k.a. add
   custom backend / data connector).
2. Point it at your backend URL (`http://localhost:8000` for local dev, or the
   public URL once deployed).
3. Workspace reads `/widgets.json` and `/apps.json`; the **Sugra Entity
   Screening** app appears with all widgets ready to use.

## Status / TODO before listing

This is a **proof of concept** to demo the offering and support the marketplace
application — not yet production.

- [ ] **Confirm upstream request/response shapes.** The POST bodies
      (`/entity/screen`, `/entity/resolve`, `/entity/screen/batch`) and table
      field names are based on catalog summaries. Verify against the live API
      and tighten `as_rows()` / add explicit `columnsDefs` for clean columns.
- [ ] Decide the trial-data story (sample dataset shown pre-key) per OpenBB's
      trial model.
- [ ] Add an `agents.json` so Copilot has first-class grounding for the
      "assess this counterparty" workflow.
- [ ] Harden auth: per-user API keys vs a single backend key.
- [ ] Deploy to a public URL and reach out to the OpenBB partnerships team to
      begin vetting/onboarding.

## How this fits the marketplace path

`openbb-sugra` (the provider package) plugs Sugra into the OpenBB **Platform**
(Python SDK). The marketplace lists **Workspace apps** — a hosted backend
serving `widgets.json` + `apps.json`, which is exactly this project. The two are
complementary: same data, two surfaces.
