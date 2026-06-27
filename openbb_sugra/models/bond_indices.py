"""Sugra Bond Indices Model."""

# pylint: disable=unused-argument

from typing import Any, Literal

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.bond_indices import (
    BondIndicesData,
    BondIndicesQueryParams,
)
from pydantic import Field, PrivateAttr

# ICE BofA index series (ID per category -> index -> index_type) published on
# FRED. Ported VERBATIM (clean-room) from the openbb_fred blueprint - openbb_fred
# is NOT a runtime dependency, so the catalog is transcribed here, not imported.
# The "us" -> "yield_curve" sub-tree fans out one series per maturity bucket.
BAML_CATEGORIES = {
    "high_yield": {
        "us": {
            "total_return": "BAMLHYH0A0HYM2TRIV",
            "yield": "BAMLH0A0HYM2EY",
            "oas": "BAMLH0A0HYM2",
            "yield_to_worst": "BAMLH0A0HYM2SYTW",
        },
        "europe": {
            "total_return": "BAMLHE00EHYITRIV",
            "yield": "BAMLHE00EHYIEY",
            "oas": "BAMLHE00EHYIOAS",
            "yield_to_worst": "BAMLHE00EHYISYTW",
        },
        "emerging": {
            "total_return": "BAMLEMHBHYCRPITRIV",
            "yield": "BAMLEMHBHYCRPIEY",
            "oas": "BAMLEMHBHYCRPIOAS",
            "yield_to_worst": "BAMLEMHBHYCRPISYTW",
        },
    },
    "us": {
        "corporate": {
            "total_return": "BAMLCC0A0CMTRIV",
            "yield": "BAMLC0A0CMEY",
            "oas": "BAMLC0A0CM",
            "yield_to_worst": "BAMLC0A0CMSYTW",
        },
        "seasoned_corporate": {
            "total_return": "",
            "yield": "DAAA,AAA10Y,AAAFF,DBAA,BAA10Y,BAAFF",
            "oas": "",
            "yield_to_worst": "",
        },
        "high_yield": {
            "total_return": "BAMLHYH0A0HYM2TRIV",
            "yield": "BAMLH0A0HYM2EY",
            "oas": "BAMLH0A0HYM2",
            "yield_to_worst": "BAMLH0A0HYM2SYTW",
        },
        "yield_curve": {
            "year1_year3": {
                "total_return": "BAMLCC1A013YTRIV",
                "yield": "BAMLC1A0C13YEY",
                "oas": "BAMLC1A0C13Y",
                "yield_to_worst": "BAMLC1A0C13YSYTW",
            },
            "year3_year5": {
                "total_return": "BAMLCC2A035YTRIV",
                "yield": "BAMLC2A0C35YEY",
                "oas": "BAMLC2A0C35Y",
                "yield_to_worst": "BAMLC2A0C35YSYTW",
            },
            "year5_year7": {
                "total_return": "BAMLCC3A057YTRIV",
                "yield": "BAMLC3A0C57YEY",
                "oas": "BAMLC3A0C57Y",
                "yield_to_worst": "BAMLC3A0C57YSYTW",
            },
            "year7_year10": {
                "total_return": "BAMLCC4A0710YTRIV",
                "yield": "BAMLC4A0C710YEY",
                "oas": "BAMLC4A0C710Y",
                "yield_to_worst": "BAMLC4A0C710YSYTW",
            },
            "year10_year15": {
                "total_return": "BAMLCC7A01015YTRIV",
                "yield": "BAMLC7A0C1015YEY",
                "oas": "BAMLC7A0C1015Y",
                "yield_to_worst": "BAMLC7A0C1015YSYTW",
            },
            "year15+": {
                "total_return": "BAMLCC8A015PYTRIV",
                "yield": "BAMLC8A0C15PYEY",
                "oas": "BAMLC8A0C15PY",
                "yield_to_worst": "BAMLC8A0C15PYSYTW",
            },
        },
        "aaa": {
            "total_return": "BAMLCC0A1AAATRIV",
            "yield": "BAMLC0A1CAAAEY",
            "oas": "BAMLC0A1CAAA",
            "yield_to_worst": "BAMLC0A1CAAASYTW",
        },
        "aa": {
            "total_return": "BAMLCC0A2AATRIV",
            "yield": "BAMLC0A2CAAEY",
            "oas": "BAMLC0A2CAA",
            "yield_to_worst": "BAMLC0A2CAASYTW",
        },
        "a": {
            "total_return": "BAMLCC0A3ATRIV",
            "yield": "BAMLC0A3CAEY",
            "oas": "BAMLC0A3CA",
            "yield_to_worst": "BAMLC0A3CASYTW",
        },
        "bbb": {
            "total_return": "BAMLCC0A4BBBTRIV",
            "yield": "BAMLC0A4CBBBEY",
            "oas": "BAMLC0A4CBBB",
            "yield_to_worst": "BAMLC0A4CBBBSYTW",
        },
        "bb": {
            "total_return": "BAMLHYH0A1BBTRIV",
            "yield": "BAMLH0A1HYBBEY",
            "oas": "BAMLH0A1HYBB",
            "yield_to_worst": "BAMLH0A1HYBBSYTW",
        },
        "b": {
            "total_return": "BAMLHYH0A2BTRIV",
            "yield": "BAMLH0A2HYBEY",
            "oas": "BAMLH0A2HYB",
            "yield_to_worst": "BAMLH0A2HYBSYTW",
        },
        "ccc": {
            # Upstream openbb_fred has a double-C typo here (BAMLH0A3HYCC /
            # ...CCSYTW) that 502s on FRED; the real CCC OAS/YTW ids are single-C.
            "total_return": "BAMLHYH0A3CMTRIV",
            "yield": "BAMLH0A3HYCEY",
            "oas": "BAMLH0A3HYC",
            "yield_to_worst": "BAMLH0A3HYCSYTW",
        },
    },
    "emerging_markets": {
        "corporate": {
            "total_return": "BAMLEMCBPITRIV",
            "yield": "BAMLEMCBPIEY",
            "yield_to_worst": "BAMLEMCBPISYTW",
            "oas": "BAMLEMCBPIOAS",
        },
        "liquid_corporate": {
            "total_return": "BAMLEMCLLCRPIUSTRIV",
            "yield": "BAMLEMCLLCRPIUSEY",
            "yield_to_worst": "BAMLEMCLLCRPIUSSYTW",
            "oas": "BAMLEMCLLCRPIUSOAS",
        },
        "crossover": {
            "total_return": "BAMLEM5BCOCRPITRIV",
            "yield": "BAMLEM5BCOCRPIEY",
            "oas": "BAMLEM5BCOCRPIOAS",
            "yield_to_worst": "BAMLEM5BCOCRPISYTW",
        },
        "public_sector": {
            "total_return": "BAMLEMPUPUBSLCRPIUSTRIV",
            "yield": "BAMLEMPUPUBSLCRPIUSEY",
            "oas": "BAMLEMPUPUBSLCRPIUSOAS",
            "yield_to_worst": "BAMLEMPUPUBSLCRPIUSSYTW",
        },
        "private_sector": {
            "total_return": "BAMLEMFSFCRPITRIV",
            "yield": "BAMLEMFSFCRPIEY",
            "oas": "BAMLEMFSFCRPIOAS",
            "yield_to_worst": "BAMLEMFSFCRPISYTW",
        },
        "non_financial": {
            "total_return": "BAMLEMNFNFLCRPIUSTRIV",
            "yield": "BAMLEMNFNFLCRPIUSEY",
            "oas": "BAMLEMNFNFLCRPIUSOAS",
            "yield_to_worst": "BAMLEMNFNFLCRPIUSSYTW",
        },
        "high_grade": {
            "total_return": "BAMLEMIBHGCRPITRIV",
            "yield": "BAMLEMIBHGCRPIEY",
            "oas": "BAMLEMIBHGCRPIOAS",
            "yield_to_worst": "BAMLEMIBHGCRPISYTW",
        },
        "high_yield": {
            "total_return": "BAMLEMHBHYCRPITRIV",
            "yield": "BAMLEMHBHYCRPIEY",
            "oas": "BAMLEMHBHYCRPIOAS",
            "yield_to_worst": "BAMLEMHBHYCRPISYTW",
        },
        "liquid_emea": {
            "total_return": "BAMLEMELLCRPIEMEAUSTRIV",
            "yield": "BAMLEMELLCRPIEMEAUSEY",
            "oas": "BAMLEMELLCRPIEMEAUSOAS",
            "yield_to_worst": "BAMLEMELLCRPIEMEAUSSYTW",
        },
        "emea": {
            "total_return": "BAMLEMRECRPIEMEATRIV",
            "yield": "BAMLEMRECRPIEMEAEY",
            "oas": "BAMLEMRECRPIEMEAOAS",
            "yield_to_worst": "BAMLEMRECRPIEMEASYTW",
        },
        "liquid_asia": {
            "total_return": "BAMLEMALLCRPIASIAUSTRIV",
            "yield": "BAMLEMALLCRPIASIAUSEY",
            "oas": "BAMLEMALLCRPIASIAUSOAS",
            "yield_to_worst": "BAMLEMALLCRPIASIAUSSYTW",
        },
        "asia": {
            "total_return": "BAMLEMRACRPIASIATRIV",
            "yield": "BAMLEMRACRPIASIAEY",
            "oas": "BAMLEMRACRPIASIAOAS",
            "yield_to_worst": "BAMLEMRACRPIASIASYTW",
        },
        "liquid_latam": {
            "total_return": "BAMLEMLLLCRPILAUSTRIV",
            "yield": "BAMLEMLLLCRPILAUSEY",
            "oas": "BAMLEMLLLCRPILAUSOAS",
            "yield_to_worst": "BAMLEMLLLCRPILAUSSYTW",
        },
        "latam": {
            "total_return": "BAMLEMRLCRPILATRIV",
            "yield": "BAMLEMRLCRPILAEY",
            "oas": "BAMLEMRLCRPILAOAS",
            "yield_to_worst": "BAMLEMRLCRPILASYTW",
        },
        "liquid_aaa": {
            "total_return": "BAMLEM1RAAA2ALCRPIUSTRIV",
            "yield": "BAMLEM1RAAA2ALCRPIUSEY",
            "oas": "BAMLEM1RAAA2ALCRPIUSOAS",
            "yield_to_worst": "BAMLEM1RAAA2ALCRPIUSSYTW",
        },
        "liquid_bbb": {
            "total_return": "BAMLEM2RBBBLCRPIUSTRIV",
            "yield": "BAMLEM2RBBBLCRPIUSEY",
            "oas": "BAMLEM2RBBBLCRPIUSOAS",
            "yield_to_worst": "BAMLEM2RBBBLCRPIUSSYTW",
        },
        "aaa": {
            "total_return": "BAMLEM1BRRAAA2ACRPITRIV",
            "yield": "BAMLEM1BRRAAA2ACRPIEY",
            "oas": "BAMLEM1BRRAAA2ACRPIOAS",
            "yield_to_worst": "BAMLEM1BRRAAA2ACRPISYTW",
        },
        "bbb": {
            "total_return": "BAMLEM2BRRBBBCRPITRIV",
            "yield": "BAMLEM2BRRBBBCRPIEY",
            "oas": "BAMLEM2BRRBBBCRPIOAS",
            "yield_to_worst": "BAMLEM2BRRBBBCRPISYTW",
        },
        "bb": {
            "total_return": "BAMLEM3BRRBBCRPITRIV",
            "yield": "BAMLEM3BRRBBCRPIEY",
            "oas": "BAMLEM3BRRBBCRPIOAS",
            "yield_to_worst": "BAMLEM3BRRBBCRPISYTW",
        },
        "b": {
            "total_return": "BAMLEM4BRRBLCRPITRIV",
            "yield": "BAMLEM4BRRBLCRPIEY",
            "oas": "BAMLEM4BRRBLCRPIOAS",
            "yield_to_worst": "BAMLEM4BRRBLCRPISYTW",
        },
    },
}

BamlCategories = Literal["high_yield", "us", "emerging_markets"]
INDEX_CHOICES = [
    "corporate",
    "seasoned_corporate",
    "liquid_corporate",
    "yield_curve",
    "crossover",
    "public_sector",
    "private_sector",
    "non_financial",
    "high_grade",
    "high_yield",
    "liquid_emea",
    "emea",
    "liquid_asia",
    "asia",
    "liquid_latam",
    "latam",
    "liquid_aaa",
    "liquid_bbb",
    "aaa",
    "aa",
    "a",
    "bbb",
    "bb",
    "b",
    "ccc",
]

_index_choices_str = "\n            ".join(INDEX_CHOICES)


class SugraBondIndicesQueryParams(BondIndicesQueryParams):
    """Sugra Bond Indices Query Parameters."""

    __json_schema_extra__ = {
        "index": {
            "multiple_items_allowed": True,
            "choices": sorted(INDEX_CHOICES),
        }
    }

    category: BamlCategories = Field(
        default="us",
        description="The type of index category. Used with 'index', default is 'us'.",
    )
    index: str = Field(
        default="yield_curve",
        description="The specific index to query."
        + " Used with 'category' and 'index_type', default is 'yield_curve'."
        + f"""
        Possible values are:
            {_index_choices_str}\n
        """,
    )
    _symbols: str | None = PrivateAttr(default=None)


class SugraBondIndicesData(BondIndicesData):
    """Sugra Bond Indices Data."""

    maturity: str | None = Field(
        default=None,
        description="The maturity range of the bond index."
        + " Only applicable when 'index' is 'yield_curve'.",
    )
    title: str = Field(
        description="The title of the index.",
    )


class SugraBondIndicesFetcher(
    Fetcher[SugraBondIndicesQueryParams, list[SugraBondIndicesData]]
):
    """Fetch ICE BofA bond index series (BAML* on FRED) from the Sugra API."""

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SugraBondIndicesQueryParams:
        """Resolve the category/index/index_type selectors to FRED series IDs."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError

        values = params.copy()
        values.setdefault("category", "us")
        values.setdefault("index", "yield_curve")
        values.setdefault("index_type", "yield")
        # `or "yield_curve"` guards an explicit index=None / empty (setdefault
        # fills only a missing key, not a present-but-None one) before the join.
        index = values["index"] or "yield_curve"
        index_str = index if isinstance(index, str) else ",".join(index)
        # Normalize and write back: the catalog keys are lowercase, callers may
        # send "OAS"/"Yield" (the standard model lowercases, but Fetcher.test
        # passes a raw dict), and `or "yield"` guards an explicit None/"".
        index_type = (values["index_type"] or "yield").lower()
        values["index_type"] = index_type

        new_index: list[str] = []
        symbols: list[str] = []
        if "yield_curve" in index_str:
            # yield_curve fans out one series per maturity bucket and is US-only.
            values["category"] = "us"
            values["index"] = "yield_curve"
            maturities_dict = BAML_CATEGORIES["us"]["yield_curve"]
            new_index = ["yield_curve"]
            symbols = [maturities_dict[m].get(index_type) for m in maturities_dict]
        else:
            category = values["category"]
            items = index if isinstance(index, list) else index_str.split(",")
            for item in items:
                sid = BAML_CATEGORIES.get(category, {}).get(item, {}).get(index_type)
                if sid:
                    symbols.append(sid)
                    new_index.append(item)

        symbols = [s for s in symbols if s]
        if not symbols:
            raise OpenBBError(
                "Error mapping the provided choices to series ID."
                " Check the category, index, and index_type combination."
            )
        values["index"] = ",".join(new_index)
        new_params = SugraBondIndicesQueryParams(**values)
        # pylint: disable=protected-access
        new_params._symbols = ",".join(symbols)
        return new_params

    @staticmethod
    async def aextract_data(
        query: SugraBondIndicesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Fetch each resolved FRED series concurrently from the Sugra API."""
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        # seasoned_corporate packs several IDs in one value - flatten on comma.
        raw = query._symbols or ""  # pylint: disable=protected-access
        ids: list[str] = []
        for token in raw.split(","):
            token = token.strip()
            if token and token not in ids:
                ids.append(token)
        return await fred_series_payloads(
            api_key, ids, start_date=query.start_date, end_date=query.end_date
        )

    @staticmethod
    def transform_data(
        query: SugraBondIndicesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraBondIndicesData]:
        """Melt per-series payloads into long rows with explicit normalization.

        NORMALIZATION: 'total_return' is an index LEVEL kept AS-IS; the percent
        index types (yield, oas, yield_to_worst) are stored as fractions (/100),
        mirroring the FRED blueprint's ``value / 100`` for non-total_return.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        if not data:
            raise EmptyDataError("The request was returned empty.")

        as_is = query.index_type == "total_return"

        # Map each yield_curve series ID back to its maturity bucket label.
        maturity_map: dict[str, str] = {}
        maturity_order: dict[str, int] = {}
        if query.index == "yield_curve":
            maturities_dict = BAML_CATEGORIES["us"]["yield_curve"]
            for order, bucket in enumerate(maturities_dict):
                sid = maturities_dict[bucket].get(query.index_type)
                if sid:
                    maturity_map[sid] = bucket
                    maturity_order[bucket] = order

        rows: list[dict] = []
        for series_id, payload in (data or {}).items():
            title = payload.get("title") if isinstance(payload, dict) else None
            maturity = maturity_map.get(series_id)
            for obs in fred_observations(payload):
                value = obs["value"] if as_is else obs["value"] / 100
                rows.append(
                    {
                        "date": obs["date"],
                        "symbol": series_id,
                        "value": value,
                        "title": title,
                        "maturity": maturity,
                    }
                )
        if not rows:
            raise EmptyDataError(
                "No data found for the given query. Try adjusting the parameters."
            )
        rows.sort(
            key=lambda r: (r["date"], maturity_order.get(r["maturity"], 0))
        )
        return [SugraBondIndicesData.model_validate(r) for r in rows]
