"""Sugra Commercial Paper Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.commercial_paper import (
    CommercialPaperData,
    CommercialPaperParams,
)
from pydantic import Field

# Each commercial-paper rate is one FRED series. The id encodes the asset
# category and the maturity: f"RIFSPP{CAT}{MAT}NB". Ported clean-room from the
# openbb_fred blueprint (openbb_fred is not a dependency, so the catalog lives
# here): asset_backed=AAAD, financial=FAAD, nonfinancial=NAAD, a2p2=NA2P2D and
# MAT in 01/07/15/30/60/90. The a2p2 category has no AAAD/FAAD/NAAD variants -
# only the NA2P2D ids exist - so the full id catalog below is authoritative.
CP_SERIES_IDS: dict[str, dict[str, str]] = {
    "RIFSPPAAAD01NB": {
        "maturity": "overnight",
        "asset": "asset_backed",
        "title": "Overnight AA Asset-Backed Commercial Paper Interest Rate",
    },
    "RIFSPPAAAD07NB": {
        "maturity": "day_7",
        "asset": "asset_backed",
        "title": "7-Day AA Asset-Backed Commercial Paper Interest Rate",
    },
    "RIFSPPAAAD15NB": {
        "maturity": "day_15",
        "asset": "asset_backed",
        "title": "15-Day AA Asset-Backed Commercial Paper Interest Rate",
    },
    "RIFSPPAAAD30NB": {
        "maturity": "day_30",
        "asset": "asset_backed",
        "title": "30-Day AA Asset-Backed Commercial Paper Interest Rate",
    },
    "RIFSPPAAAD60NB": {
        "maturity": "day_60",
        "asset": "asset_backed",
        "title": "60-Day AA Asset-Backed Commercial Paper Interest Rate",
    },
    "RIFSPPAAAD90NB": {
        "maturity": "day_90",
        "asset": "asset_backed",
        "title": "90-Day AA Asset-Backed Commercial Paper Interest Rate",
    },
    "RIFSPPFAAD01NB": {
        "maturity": "overnight",
        "asset": "financial",
        "title": "Overnight AA Financial Commercial Paper Interest Rate",
    },
    "RIFSPPFAAD07NB": {
        "maturity": "day_7",
        "asset": "financial",
        "title": "7-Day AA Financial Commercial Paper Interest Rate",
    },
    "RIFSPPFAAD15NB": {
        "maturity": "day_15",
        "asset": "financial",
        "title": "15-Day AA Financial Commercial Paper Interest Rate",
    },
    "RIFSPPFAAD30NB": {
        "maturity": "day_30",
        "asset": "financial",
        "title": "30-Day AA Financial Commercial Paper Interest Rate",
    },
    "RIFSPPFAAD60NB": {
        "maturity": "day_60",
        "asset": "financial",
        "title": "60-Day AA Financial Commercial Paper Interest Rate",
    },
    "RIFSPPFAAD90NB": {
        "maturity": "day_90",
        "asset": "financial",
        "title": "90-Day AA Financial Commercial Paper Interest Rate",
    },
    "RIFSPPNAAD01NB": {
        "maturity": "overnight",
        "asset": "nonfinancial",
        "title": "Overnight AA Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNAAD07NB": {
        "maturity": "day_7",
        "asset": "nonfinancial",
        "title": "7-Day AA Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNAAD15NB": {
        "maturity": "day_15",
        "asset": "nonfinancial",
        "title": "15-Day AA Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNAAD30NB": {
        "maturity": "day_30",
        "asset": "nonfinancial",
        "title": "30-Day AA Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNAAD60NB": {
        "maturity": "day_60",
        "asset": "nonfinancial",
        "title": "60-Day AA Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNAAD90NB": {
        "maturity": "day_90",
        "asset": "nonfinancial",
        "title": "90-Day AA Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNA2P2D01NB": {
        "maturity": "overnight",
        "asset": "a2p2",
        "title": "Overnight A2/P2 Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNA2P2D07NB": {
        "maturity": "day_7",
        "asset": "a2p2",
        "title": "7-Day A2/P2 Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNA2P2D15NB": {
        "maturity": "day_15",
        "asset": "a2p2",
        "title": "15-Day A2/P2 Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNA2P2D30NB": {
        "maturity": "day_30",
        "asset": "a2p2",
        "title": "30-Day A2/P2 Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNA2P2D60NB": {
        "maturity": "day_60",
        "asset": "a2p2",
        "title": "60-Day A2/P2 Nonfinancial Commercial Paper Interest Rate",
    },
    "RIFSPPNA2P2D90NB": {
        "maturity": "day_90",
        "asset": "a2p2",
        "title": "90-Day A2/P2 Nonfinancial Commercial Paper Interest Rate",
    },
}
ALL_IDS = list(CP_SERIES_IDS)

# Selector token -> id fragment. CAT_DICT/MAT_DICT build the id; ported verbatim
# from the openbb_fred blueprint id construction (f"RIFSPP{CAT}{MAT}NB").
_CAT_DICT = {
    "asset_backed": "AAAD",
    "financial": "FAAD",
    "nonfinancial": "NAAD",
    "a2p2": "NA2P2D",
}
_MAT_DICT = {
    "overnight": "01",
    "7d": "07",
    "15d": "15",
    "30d": "30",
    "60d": "60",
    "90d": "90",
}
# Output ordering for stable long rows (matches the standard model presentation).
_ASSET_ORDER = {"asset_backed": 0, "financial": 1, "nonfinancial": 2, "a2p2": 3}
_MATURITY_ORDER = {
    "overnight": 0,
    "day_7": 1,
    "day_15": 2,
    "day_30": 3,
    "day_60": 4,
    "day_90": 5,
}


class SugraCommercialPaperQueryParams(CommercialPaperParams):
    """Sugra Commercial Paper Query Parameters."""

    __json_schema_extra__ = {
        "maturity": {
            "multiple_items_allowed": True,
            "choices": ["all", "overnight", "7d", "15d", "30d", "60d", "90d"],
        },
        "category": {
            "multiple_items_allowed": True,
            "choices": ["all", "asset_backed", "financial", "nonfinancial", "a2p2"],
        },
    }

    maturity: str | Literal["all", "overnight", "7d", "15d", "30d", "60d", "90d"] = (
        Field(default="all", description="A target maturity.")
    )
    category: (
        str | Literal["all", "asset_backed", "financial", "nonfinancial", "a2p2"]
    ) = Field(default="all", description="The category of asset.")


class SugraCommercialPaperData(CommercialPaperData):
    """Sugra Commercial Paper Data."""

    asset_type: Literal["asset_backed", "financial", "nonfinancial", "a2p2"] = Field(
        description="The category of asset."
    )


class SugraCommercialPaperFetcher(
    Fetcher[SugraCommercialPaperQueryParams, list[SugraCommercialPaperData]]
):
    """Fetch AA commercial paper interest rates (RIFSPP* series) from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraCommercialPaperQueryParams:
        """Transform the query parameters."""
        return SugraCommercialPaperQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraCommercialPaperQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the selected commercial-paper series (one per id) from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        if query.maturity == "all" and query.category == "all":
            ids = ALL_IDS
        else:
            maturities = query.maturity.split(",")
            categories = query.category.split(",")
            if "all" in categories:
                categories = list(_CAT_DICT)
            if "all" in maturities:
                maturities = list(_MAT_DICT)
            ids = []
            for cat in categories:
                for mat in maturities:
                    series_id = f"RIFSPP{_CAT_DICT.get(cat)}{_MAT_DICT.get(mat)}NB"
                    # a2p2 only exists for the NA2P2D ids; skip any built id that
                    # is not a real FRED series (defensive, also drops bad tokens).
                    # `not in ids` avoids a redundant fetch on duplicate tokens.
                    if series_id in CP_SERIES_IDS and series_id not in ids:
                        ids.append(series_id)
        return await fred_series_payloads(
            api_key, ids, start_date=query.start_date, end_date=query.end_date
        )

    @staticmethod
    def transform_data(
        query: SugraCommercialPaperQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraCommercialPaperData]:
        """Melt the per-series payloads into long rows. The rate is a fraction (value / 100)."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        rows: list[dict] = []
        for series_id, payload in (data or {}).items():
            meta = CP_SERIES_IDS.get(series_id, {})
            maturity = meta.get("maturity", series_id)
            asset_type = meta.get("asset")
            # Prefer the live series title; fall back to the catalog title.
            title = (
                payload.get("title") if isinstance(payload, dict) else None
            ) or meta.get("title")
            for obs in fred_observations(payload):
                rows.append(
                    {
                        "date": obs["date"],
                        "symbol": series_id,
                        # rate carries x-frontend_multiply:100 -> store the
                        # fraction (value / 100); the other fields are labels.
                        "rate": obs["value"] / 100,
                        "maturity": maturity,
                        "asset_type": asset_type,
                        "title": title,
                    }
                )
        if not rows:
            raise EmptyDataError("No commercial paper observations returned.")
        rows.sort(
            key=lambda r: (
                r["date"],
                _ASSET_ORDER.get(r["asset_type"], 99),
                _MATURITY_ORDER.get(r["maturity"], 99),
            )
        )
        return [SugraCommercialPaperData.model_validate(r) for r in rows]
