"""Sugra Manufacturing Outlook - Texas - Model."""

# pylint: disable=unused-argument

from typing import Any, Literal
from warnings import warn

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.manufacturing_outlook_texas import (
    ManufacturingOutlookTexasData,
    ManufacturingOutlookTexasQueryParams,
)
from pydantic import Field, field_validator

# Texas (Dallas Fed) manufacturing survey. Each topic has a current and a future
# variant; each variant has four FRED series (the diffusion index plus the three
# percent-reporting splits). Catalog ported clean-room VERBATIM from the
# openbb_fred blueprint (openbb_fred is NOT a dependency, so the nested dict lives
# here). Keys are the prefixed topic; the public selector uses the unprefixed name.
TEXAS_MANUFACTURING_OUTLOOK: dict[str, dict[str, str]] = {
    "current_business_activity": {
        "diffusion_index": "BACTSAMFRBDAL",
        "percent_reporting_increase": "BACTISAMFRBDAL",
        "percent_reporting_decrease": "BACTDSAMFRBDAL",
        "percent_reporting_no_change": "BACTNSAMFRBDAL",
    },
    "future_business_activity": {
        "diffusion_index": "FBACTSAMFRBDAL",
        "percent_reporting_increase": "FBACTISAMFRBDAL",
        "percent_reporting_decrease": "FBACTDSAMFRBDAL",
        "percent_reporting_no_change": "FBACTNSAMFRBDAL",
    },
    "current_business_outlook": {
        "diffusion_index": "COLKSAMFRBDAL",
        "percent_reporting_increase": "COLKISAMFRBDAL",
        "percent_reporting_decrease": "COLKDSAMFRBDAL",
        "percent_reporting_no_change": "COLKNSAMFRBDAL",
    },
    "future_business_outlook": {
        "diffusion_index": "FCOLKSAMFRBDAL",
        "percent_reporting_increase": "FCOLKISAMFRBDAL",
        "percent_reporting_decrease": "FCOLKDSAMFRBDAL",
        "percent_reporting_no_change": "FCOLKNSAMFRBDAL",
    },
    "current_capex": {
        "diffusion_index": "CEXPSAMFRBDAL",
        "percent_reporting_increase": "CEXPISAMFRBDAL",
        "percent_reporting_decrease": "CEXPDSAMFRBDAL",
        "percent_reporting_no_change": "CEXPNSAMFRBDAL",
    },
    "future_capex": {
        "diffusion_index": "FCEXPSAMFRBDAL",
        "percent_reporting_increase": "FCEXPISAMFRBDAL",
        "percent_reporting_decrease": "FCEXPDSAMFRBDAL",
        "percent_reporting_no_change": "FCEXPNSAMFRBDAL",
    },
    "current_prices_paid": {
        "diffusion_index": "PRMSAMFRBDAL",
        "percent_reporting_increase": "PRMISAMFRBDAL",
        "percent_reporting_decrease": "PRMDSAMFRBDAL",
        "percent_reporting_no_change": "PRMNSAMFRBDAL",
    },
    "future_prices_paid": {
        "diffusion_index": "FPRMSAMFRBDAL",
        "percent_reporting_increase": "FPRMISAMFRBDAL",
        "percent_reporting_decrease": "FPRMDSAMFRBDAL",
        "percent_reporting_no_change": "FPRMNSAMFRBDAL",
    },
    "current_production": {
        "diffusion_index": "PRODSAMFRBDAL",
        "percent_reporting_increase": "PRODISAMFRBDAL",
        "percent_reporting_decrease": "PRODDSAMFRBDAL",
        "percent_reporting_no_change": "PRODNSAMFRBDAL",
    },
    "future_production": {
        "diffusion_index": "FPRODSAMFRBDAL",
        "percent_reporting_increase": "FPRODISAMFRBDAL",
        "percent_reporting_decrease": "FPRODDSAMFRBDAL",
        "percent_reporting_no_change": "FPRODNSAMFRBDAL",
    },
    "current_inventory": {
        "diffusion_index": "FGISAMFRBDAL",
        "percent_reporting_increase": "FGIISAMFRBDAL",
        "percent_reporting_decrease": "FGIDSAMFRBDAL",
        "percent_reporting_no_change": "FGINSAMFRBDAL",
    },
    "future_inventory": {
        "diffusion_index": "FFGISAMFRBDAL",
        "percent_reporting_increase": "FFGIISAMFRBDAL",
        "percent_reporting_decrease": "FFGIDSAMFRBDAL",
        "percent_reporting_no_change": "FFGINSAMFRBDAL",
    },
    "current_new_orders": {
        "diffusion_index": "VNWOSAMFRBDAL",
        "percent_reporting_increase": "VNWOISAMFRBDAL",
        "percent_reporting_decrease": "VNWODSAMFRBDAL",
        "percent_reporting_no_change": "VNWONSAMFRBDAL",
    },
    "future_new_orders": {
        "diffusion_index": "FVNWOSAMFRBDAL",
        "percent_reporting_increase": "FVNWOISAMFRBDAL",
        "percent_reporting_decrease": "FVNWODSAMFRBDAL",
        "percent_reporting_no_change": "FVNWONSAMFRBDAL",
    },
    "current_new_orders_growth": {
        "diffusion_index": "GROSAMFRBDAL",
        "percent_reporting_increase": "GROISAMFRBDAL",
        "percent_reporting_decrease": "GRODSAMFRBDAL",
        "percent_reporting_no_change": "GRONSAMFRBDAL",
    },
    "future_new_orders_growth": {
        "diffusion_index": "FGROSAMFRBDAL",
        "percent_reporting_increase": "FGROISAMFRBDAL",
        "percent_reporting_decrease": "FGRODSAMFRBDAL",
        "percent_reporting_no_change": "FGRONSAMFRBDAL",
    },
    "current_unfilled_orders": {
        "diffusion_index": "UFILSAMFRBDAL",
        "percent_reporting_increase": "UFILISAMFRBDAL",
        "percent_reporting_decrease": "UFILDSAMFRBDAL",
        "percent_reporting_no_change": "UFILNSAMFRBDAL",
    },
    "future_unfilled_orders": {
        "diffusion_index": "FUFILSAMFRBDAL",
        "percent_reporting_increase": "FUFILISAMFRBDAL",
        "percent_reporting_decrease": "FUFILDSAMFRBDAL",
        "percent_reporting_no_change": "FUFILNSAMFRBDAL",
    },
    "current_shipments": {
        "diffusion_index": "VSHPSAMFRBDAL",
        "percent_reporting_increase": "VSHPISAMFRBDAL",
        "percent_reporting_decrease": "VSHPDSAMFRBDAL",
        "percent_reporting_no_change": "VSHPNSAMFRBDAL",
    },
    "future_shipments": {
        "diffusion_index": "FVSHPSAMFRBDAL",
        "percent_reporting_increase": "FVSHPISAMFRBDAL",
        "percent_reporting_decrease": "FVSHPDSAMFRBDAL",
        "percent_reporting_no_change": "FVSHPNSAMFRBDAL",
    },
    "current_delivery_time": {
        "diffusion_index": "DTMSAMFRBDAL",
        "percent_reporting_increase": "DTMISAMFRBDAL",
        "percent_reporting_decrease": "DTMDSAMFRBDAL",
        "percent_reporting_no_change": "DTMNSAMFRBDAL",
    },
    "future_delivery_time": {
        "diffusion_index": "FDTMSAMFRBDAL",
        "percent_reporting_increase": "FDTMISAMFRBDAL",
        "percent_reporting_decrease": "FDTMDSAMFRBDAL",
        "percent_reporting_no_change": "FDTMNSAMFRBDAL",
    },
    "current_employment": {
        "diffusion_index": "NEMPSAMFRBDAL",
        "percent_reporting_increase": "NEMPISAMFRBDAL",
        "percent_reporting_decrease": "NEMPDSAMFRBDAL",
        "percent_reporting_no_change": "NEMPNSAMFRBDAL",
    },
    "future_employment": {
        "diffusion_index": "FNEMPSAMFRBDAL",
        "percent_reporting_increase": "FNEMPISAMFRBDAL",
        "percent_reporting_decrease": "FNEMPDSAMFRBDAL",
        "percent_reporting_no_change": "FNEMPNSAMFRBDAL",
    },
    "current_wages": {
        "diffusion_index": "WGSSAMFRBDAL",
        "percent_reporting_increase": "WGSISAMFRBDAL",
        "percent_reporting_decrease": "WGSDSAMFRBDAL",
        "percent_reporting_no_change": "WGSNSAMFRBDAL",
    },
    "future_wages": {
        "diffusion_index": "FWGSSAMFRBDAL",
        "percent_reporting_increase": "FWGSISAMFRBDAL",
        "percent_reporting_decrease": "FWGSDSAMFRBDAL",
        "percent_reporting_no_change": "FWGSNSAMFRBDAL",
    },
    "current_hours_worked": {
        "diffusion_index": "AVGWKSAMFRBDAL",
        "percent_reporting_increase": "AVGWKISAMFRBDAL",
        "percent_reporting_decrease": "AVGWKDSAMFRBDAL",
        "percent_reporting_no_change": "AVGWKNSAMFRBDAL",
    },
    "future_hours_worked": {
        "diffusion_index": "FAVGWKSAMFRBDAL",
        "percent_reporting_increase": "FAVGWKISAMFRBDAL",
        "percent_reporting_decrease": "FAVGWKDSAMFRBDAL",
        "percent_reporting_no_change": "FAVGWKNSAMFRBDAL",
    },
}

# Reverse lookups: FRED code -> output field (subtopic) and -> prefixed topic.
ID_TO_FIELD: dict[str, str] = {}
ID_TO_TOPIC: dict[str, str] = {}
for _topic, _subtopics in TEXAS_MANUFACTURING_OUTLOOK.items():
    for _subtopic, _code in _subtopics.items():
        ID_TO_FIELD[_code] = _subtopic
        ID_TO_TOPIC[_code] = _topic

# Stable presentation order for the (date, topic) rows: catalog key order.
_TOPIC_ORDER = {topic: i for i, topic in enumerate(TEXAS_MANUFACTURING_OUTLOOK)}

# Public selector choices (unprefixed); each maps to a current_+future_ pair.
TEXAS_MANUFACTURING_OUTLOOK_CHOICES = [
    "business_activity",
    "business_outlook",
    "capex",
    "prices_paid",
    "production",
    "inventory",
    "new_orders",
    "new_orders_growth",
    "unfilled_orders",
    "shipments",
    "delivery_time",
    "employment",
    "wages",
    "hours_worked",
]

TexasManufacturingOutlookChoices = Literal[
    "business_activity",
    "business_outlook",
    "capex",
    "prices_paid",
    "production",
    "inventory",
    "new_orders",
    "new_orders_growth",
    "unfilled_orders",
    "shipments",
    "delivery_time",
    "employment",
    "wages",
    "hours_worked",
]


class SugraManufacturingOutlookTexasQueryParams(ManufacturingOutlookTexasQueryParams):
    """Sugra Manufacturing Outlook - Texas - Query Parameters."""

    __json_schema_extra__ = {
        "topic": {
            "multiple_items_allowed": True,
            "choices": TEXAS_MANUFACTURING_OUTLOOK_CHOICES,
        }
    }

    topic: TexasManufacturingOutlookChoices | str = Field(
        default="new_orders_growth",
        description="The topic for the survey response.",
    )

    @field_validator("topic", mode="before", check_fields=False)
    @classmethod
    def validate_topic(cls, v):
        """Validate topic, dropping unknown tokens and defaulting if empty."""
        if v is None:
            return "new_orders_growth"
        topics: list = v if isinstance(v, list) else str(v).split(",")
        new_topics: list = []
        for topic in topics:
            topic = topic.strip()
            if topic in TEXAS_MANUFACTURING_OUTLOOK_CHOICES:
                new_topics.append(topic)
            elif topic:
                warn(f"Invalid topic: {topic}")
        if not new_topics:
            new_topics = ["new_orders_growth"]
        return ",".join(new_topics)


class SugraManufacturingOutlookTexasData(ManufacturingOutlookTexasData):
    """Sugra Manufacturing Outlook - Texas - Data."""


class SugraManufacturingOutlookTexasFetcher(
    Fetcher[
        SugraManufacturingOutlookTexasQueryParams,
        list[SugraManufacturingOutlookTexasData],
    ]
):
    """Fetch the Dallas Fed Texas manufacturing survey (SAMFRBDAL series)."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraManufacturingOutlookTexasQueryParams:
        """Transform the query parameters."""
        return SugraManufacturingOutlookTexasQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraManufacturingOutlookTexasQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Return the selected topics' FRED series from the Sugra API.

        A DEFAULT call (topic ``new_orders_growth``) fetches only that topic's
        current_+future_ subtopics - eight series, selector-bounded - not the
        full catalog.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        ids: list[str] = []
        for topic in query.topic.split(","):
            for prefix in ("current_", "future_"):
                for code in TEXAS_MANUFACTURING_OUTLOOK[prefix + topic].values():
                    if code not in ids:
                        ids.append(code)
        return await fred_series_payloads(
            api_key, ids, start_date=query.start_date, end_date=query.end_date
        )

    @staticmethod
    def transform_data(
        query: SugraManufacturingOutlookTexasQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraManufacturingOutlookTexasData]:
        """Melt the per-series payloads and group by (date, topic) into long rows."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        # Group each topic's four subtopic series back into one row per
        # (date, prefixed-topic). The diffusion_index has no x-frontend_multiply
        # -> stored as-is; the three percent_reporting_* fields carry
        # x-frontend_multiply:100 -> stored as the fraction (value / 100).
        grouped: dict[tuple[str, str], dict] = {}
        for series_id, payload in (data or {}).items():
            field = ID_TO_FIELD.get(series_id)
            topic = ID_TO_TOPIC.get(series_id)
            if field is None or topic is None:
                continue
            for obs in fred_observations(payload):
                key = (obs["date"], topic)
                row = grouped.setdefault(
                    key, {"date": obs["date"], "topic": topic}
                )
                if field == "diffusion_index":
                    row[field] = obs["value"]
                else:
                    row[field] = obs["value"] / 100

        if not grouped:
            raise EmptyDataError(
                "No Texas manufacturing outlook observations returned."
            )

        rows = sorted(
            grouped.values(),
            key=lambda r: (r["date"], _TOPIC_ORDER.get(r["topic"], 99)),
        )
        return [
            SugraManufacturingOutlookTexasData.model_validate(r) for r in rows
        ]
