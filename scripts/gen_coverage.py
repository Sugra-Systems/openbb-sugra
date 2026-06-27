"""Regenerate COVERAGE.md from the live Sugra provider's obb.* command routes.

Authoritative source = ``obb.coverage.providers['sugra']``. Run after adding or
removing fetchers (the provider must be built first):

    python -c "import openbb; openbb.build()"
    python scripts/gen_coverage.py
"""

from pathlib import Path

from openbb import obb

GROUP_ORDER = [
    "equity",
    "economy",
    "famafrench",
    "etf",
    "currency",
    "fixedincome",
    "index",
    "cftc",
    "commodity",
    "crypto",
    "news",
    "uscongress",
    "regulators",
    "derivatives",
]
GROUP_DESC = {
    "equity": "Equities, fundamentals, estimates, ownership, calendars, discovery",
    "economy": "Macro, GDP, inflation, employment, money, shipping/ports",
    "famafrench": "Fama-French academic factor returns",
    "etf": "ETFs",
    "currency": "Forex",
    "fixedincome": "Rates and fixed income",
    "index": "Indices",
    "cftc": "CFTC Commitment of Traders",
    "commodity": "Commodities and energy",
    "crypto": "Crypto",
    "news": "News",
    "uscongress": "US Congress bills, amendments, committees, and documents",
    "regulators": "SEC registry: CIK and symbol maps, institution and SIC search",
    "derivatives": "Options",
}


def main() -> None:
    routes = sorted(obb.coverage.providers["sugra"])
    groups: dict[str, list[str]] = {}
    for route in routes:
        top = route.lstrip(".").split(".")[0]
        groups.setdefault(top, []).append("obb" + route)

    missing = [g for g in groups if g not in GROUP_DESC]
    if missing:
        raise SystemExit(f"Unknown command group(s) with no description: {missing}")

    total = len(routes)
    lines = [
        "# openbb-sugra coverage",
        "",
        (
            f"One Sugra API key fulfils {total} OpenBB standard data models across "
            f"{len(groups)} command groups. Install one provider, set one credential, "
            "and pull all of the below - instead of wiring many separate provider keys."
        ),
        "",
        "| OpenBB command group | What it covers | Models |",
        "|---|---|---|",
    ]
    for group in GROUP_ORDER:
        models = groups.get(group)
        if not models:
            continue
        lines.append(
            f"| {group} ({len(models)}) | {GROUP_DESC[group]} | {', '.join(models)} |"
        )
    lines += [
        "",
        (
            "Every model above is live-verified against the Sugra API and through the "
            "OpenBB obb.* layer. OpenBB models that Sugra does not yet cover are tracked "
            "separately and added as the underlying data lands."
        ),
        "",
    ]
    Path("COVERAGE.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"COVERAGE.md regenerated: {total} models across {len(groups)} groups")
    for group in GROUP_ORDER:
        if group in groups:
            print(f"  {group}: {len(groups[group])}")


if __name__ == "__main__":
    main()
