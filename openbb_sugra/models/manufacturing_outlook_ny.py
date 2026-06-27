"""Sugra Manufacturing Outlook - New York - Model."""

# pylint: disable=unused-argument

from typing import Any, Literal
from warnings import warn

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.manufacturing_outlook_texas import (
    ManufacturingOutlookTexasData,
    ManufacturingOutlookTexasQueryParams,
)
from pydantic import Field, field_validator

# Empire State (New York) Manufacturing Survey diffusion indices and the
# share-of-respondents breakdowns, one FRED series per (topic, seasonality,
# field). Ported clean-room from the openbb_fred blueprint (openbb_fred is not
# a dependency, so the catalog lives here). Keys are the full topic
# (current_/future_ + concept); each maps to seasonally-adjusted (sa) and
# not-seasonally-adjusted (not_sa) variants, each holding the four field ids.
NY_MANUFACTURING_OUTLOOK = {
    "current_hours_worked": {
        "sa": {
            "diffusion_index": "AWCDISA066MSFRBNY",
            "percent_reporting_increase": "AWCISA156MSFRBNY",
            "percent_reporting_decrease": "AWCDSA156MSFRBNY",
            "percent_reporting_no_change": "AWCNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "AWCDINA066MNFRBNY",
            "percent_reporting_increase": "AWCINA156MNFRBNY",
            "percent_reporting_decrease": "AWCDNA156MNFRBNY",
            "percent_reporting_no_change": "AWCNNA156MNFRBNY",
        },
    },
    "future_hours_worked": {
        "sa": {
            "diffusion_index": "AWFDISA066MSFRBNY",
            "percent_reporting_increase": "AWFISA156MSFRBNY",
            "percent_reporting_decrease": "AWFDSA156MSFRBNY",
            "percent_reporting_no_change": "AWFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "AWFDINA066MNFRBNY",
            "percent_reporting_increase": "AWFINA156MNFRBNY",
            "percent_reporting_decrease": "AWFDNA156MNFRBNY",
            "percent_reporting_no_change": "AWFNNA156MNFRBNY",
        },
    },
    "current_business_outlook": {
        "sa": {
            "diffusion_index": "GACDISA066MSFRBNY",
            "percent_reporting_increase": "GACISA156MSFRBNY",
            "percent_reporting_decrease": "GACDSA156MSFRBNY",
            "percent_reporting_no_change": "GACNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "GACDINA066MNFRBNY",
            "percent_reporting_increase": "GACINA156MNFRBNY",
            "percent_reporting_decrease": "GACDNA156MNFRBNY",
            "percent_reporting_no_change": "GACNNA156MNFRBNY",
        },
    },
    "future_business_outlook": {
        "sa": {
            "diffusion_index": "GAFDISA066MSFRBNY",
            "percent_reporting_increase": "GAFISA156MSFRBNY",
            "percent_reporting_decrease": "GAFDSA156MSFRBNY",
            "percent_reporting_no_change": "GAFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "GAFDINA066MNFRBNY",
            "percent_reporting_increase": "GAFINA156MNFRBNY",
            "percent_reporting_decrease": "GAFDNA156MNFRBNY",
            "percent_reporting_no_change": "GAFNNA156MNFRBNY",
        },
    },
    "current_employment": {
        "sa": {
            "diffusion_index": "NECDISA066MSFRBNY",
            "percent_reporting_increase": "NECISA156MSFRBNY",
            "percent_reporting_decrease": "NECDSA156MSFRBNY",
            "percent_reporting_no_change": "NECNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "NECDINA066MNFRBNY",
            "percent_reporting_increase": "NECINA156MNFRBNY",
            "percent_reporting_decrease": "NECDNA156MNFRBNY",
            "percent_reporting_no_change": "NECNNA156MNFRBNY",
        },
    },
    "future_employment": {
        "sa": {
            "diffusion_index": "NEFDISA066MSFRBNY",
            "percent_reporting_increase": "NEFISA156MSFRBNY",
            "percent_reporting_decrease": "NEFDSA156MSFRBNY",
            "percent_reporting_no_change": "NEFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "NEFDINA066MNFRBNY",
            "percent_reporting_increase": "NEFINA156MNFRBNY",
            "percent_reporting_decrease": "NEFDNA156MNFRBNY",
            "percent_reporting_no_change": "NEFNNA156MNFRBNY",
        },
    },
    "current_inventories": {
        "sa": {
            "diffusion_index": "IVCDISA066MSFRBNY",
            "percent_reporting_increase": "IVCISA156MSFRBNY",
            "percent_reporting_decrease": "IVCDSA156MSFRBNY",
            "percent_reporting_no_change": "IVCNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "IVCDINA066MNFRBNY",
            "percent_reporting_increase": "IVCINA156MNFRBNY",
            "percent_reporting_decrease": "IVCDNA156MNFRBNY",
            "percent_reporting_no_change": "IVCNNA156MNFRBNY",
        },
    },
    "future_inventories": {
        "sa": {
            "diffusion_index": "IVFDISA066MSFRBNY",
            "percent_reporting_increase": "IVFISA156MSFRBNY",
            "percent_reporting_decrease": "IVFDSA156MSFRBNY",
            "percent_reporting_no_change": "IVFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "IVFDINA066MNFRBNY",
            "percent_reporting_increase": "IVFINA156MNFRBNY",
            "percent_reporting_decrease": "IVFDNA156MNFRBNY",
            "percent_reporting_no_change": "IVFNNA156MNFRBNY",
        },
    },
    "current_prices_received": {
        "sa": {
            "diffusion_index": "PRCDISA066MSFRBNY",
            "percent_reporting_increase": "PRCISA156MSFRBNY",
            "percent_reporting_decrease": "PRCDSA156MSFRBNY",
            "percent_reporting_no_change": "PRCNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "PRCDINA066MNEMFRBNY",
            "percent_reporting_increase": "PRCINA156MNEMFRBNY",
            "percent_reporting_decrease": "PRCDNA156MNEMFRBNY",
            "percent_reporting_no_change": "PRCNNA156MNEMFRBNY",
        },
    },
    "future_prices_received": {
        "sa": {
            "diffusion_index": "PRFDISA066MSFRBNY",
            "percent_reporting_increase": "PRFISA156MSFRBNY",
            "percent_reporting_decrease": "PRFDSA156MSFRBNY",
            "percent_reporting_no_change": "PRFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "PRFDINA066MNEMFRBNY",
            "percent_reporting_increase": "PRFINA156MNEMFRBNY",
            "percent_reporting_decrease": "PRFDNA156MNEMFRBNY",
            "percent_reporting_no_change": "PRFNNA156MNEMFRBNY",
        },
    },
    "current_prices_paid": {
        "sa": {
            "diffusion_index": "PPCDISA066MSFRBNY",
            "percent_reporting_increase": "PPCISA156MSFRBNY",
            "percent_reporting_decrease": "PPCDSA156MSFRBNY",
            "percent_reporting_no_change": "PPCNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "PPCDINA066MNEMFRBNY",
            "percent_reporting_increase": "PPCINA156MNEMFRBNY",
            "percent_reporting_decrease": "PPCDNA156MNEMFRBNY",
            "percent_reporting_no_change": "PPCNNA156MNEMFRBNY",
        },
    },
    "future_prices_paid": {
        "sa": {
            "diffusion_index": "PPFDISA066MSFRBNY",
            "percent_reporting_increase": "PPFISA156MSFRBNY",
            "percent_reporting_decrease": "PPFDSA156MSFRBNY",
            "percent_reporting_no_change": "PPFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "PPFDINA066MNEMFRBNY",
            "percent_reporting_increase": "PPFINA156MNEMFRBNY",
            "percent_reporting_decrease": "PPFDNA156MNEMFRBNY",
            "percent_reporting_no_change": "PPFNNA156MNEMFRBNY",
        },
    },
    "future_capex": {
        "sa": {
            "diffusion_index": "CEFDISA066MSFRBNY",
            "percent_reporting_increase": "CEFISA156MSFRBNY",
            "percent_reporting_decrease": "CEFDSA156MSFRBNY",
            "percent_reporting_no_change": "CEFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "CEFDINA066MNFRBNY",
            "percent_reporting_increase": "CEFINA156MNFRBNY",
            "percent_reporting_decrease": "CEFDNA156MNFRBNY",
            "percent_reporting_no_change": "CEFNNA156MNFRBNY",
        },
    },
    "current_unfilled_orders": {
        "sa": {
            "diffusion_index": "UOCDISA066MSFRBNY",
            "percent_reporting_increase": "UOCISA156MSFRBNY",
            "percent_reporting_decrease": "UOCDSA156MSFRBNY",
            "percent_reporting_no_change": "UOCNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "UOCDINA066MNFRBNY",
            "percent_reporting_increase": "UOCINA156MNFRBNY",
            "percent_reporting_decrease": "UOCDNA156MNFRBNY",
            "percent_reporting_no_change": "UOCNNA156MNFRBNY",
        },
    },
    "future_unfilled_orders": {
        "sa": {
            "diffusion_index": "UOFDISA066MSFRBNY",
            "percent_reporting_increase": "UOFISA156MSFRBNY",
            "percent_reporting_decrease": "UOFDSA156MSFRBNY",
            "percent_reporting_no_change": "UOFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "UOFDINA066MNFRBNY",
            "percent_reporting_increase": "UOFINA156MNFRBNY",
            "percent_reporting_decrease": "UOFDNA156MNFRBNY",
            "percent_reporting_no_change": "UOFNNA156MNFRBNY",
        },
    },
    "current_new_orders": {
        "sa": {
            # Upstream openbb_fred wrongly reuses the not-SA diffusion id here;
            # the real seasonally-adjusted new-orders series is NOCDISA066MSFRBNY.
            "diffusion_index": "NOCDISA066MSFRBNY",
            "percent_reporting_increase": "NOCISA156MSFRBNY",
            "percent_reporting_decrease": "NOCDSA156MSFRBNY",
            "percent_reporting_no_change": "NOCNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "NOCDINA066MNFRBNY",
            "percent_reporting_increase": "NOCINA156MNFRBNY",
            "percent_reporting_decrease": "NOCDNA156MNFRBNY",
            "percent_reporting_no_change": "NOCNNA156MNFRBNY",
        },
    },
    "future_new_orders": {
        "sa": {
            "diffusion_index": "NOFDISA066MSFRBNY",
            "percent_reporting_increase": "NOFISA156MSFRBNY",
            "percent_reporting_decrease": "NOFDSA156MSFRBNY",
            "percent_reporting_no_change": "NOFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "NOFDINA066MNFRBNY",
            "percent_reporting_increase": "NOFINA156MNFRBNY",
            "percent_reporting_decrease": "NOFDNA156MNFRBNY",
            "percent_reporting_no_change": "NOFNNA156MNFRBNY",
        },
    },
    "current_shipments": {
        "sa": {
            "diffusion_index": "SHCDISA066MSFRBNY",
            "percent_reporting_increase": "SHCISA156MSFRBNY",
            "percent_reporting_decrease": "SHCDSA156MSFRBNY",
            "percent_reporting_no_change": "SHCNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "SHCDINA066MNFRBNY",
            "percent_reporting_increase": "SHCINA156MNFRBNY",
            "percent_reporting_decrease": "SHCDNA156MNFRBNY",
            "percent_reporting_no_change": "SHCNNA156MNFRBNY",
        },
    },
    "future_shipments": {
        "sa": {
            "diffusion_index": "SHFDISA066MSFRBNY",
            "percent_reporting_increase": "SHFISA156MSFRBNY",
            "percent_reporting_decrease": "SHFDSA156MSFRBNY",
            "percent_reporting_no_change": "SHFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "SHFDINA066MNFRBNY",
            "percent_reporting_increase": "SHFINA156MNFRBNY",
            "percent_reporting_decrease": "SHFDNA156MNFRBNY",
            "percent_reporting_no_change": "SHFNNA156MNFRBNY",
        },
    },
    "current_delivery_times": {
        "sa": {
            "diffusion_index": "DTCDISA066MSFRBNY",
            "percent_reporting_increase": "DTCISA156MSFRBNY",
            "percent_reporting_decrease": "DTCDSA156MSFRBNY",
            "percent_reporting_no_change": "DTCNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "DTCDINA066MNFRBNY",
            "percent_reporting_increase": "DTCINA156MNFRBNY",
            "percent_reporting_decrease": "DTCDNA156MNFRBNY",
            "percent_reporting_no_change": "DTCNNA156MNFRBNY",
        },
    },
    "future_delivery_times": {
        "sa": {
            "diffusion_index": "DTFDISA066MSFRBNY",
            "percent_reporting_increase": "DTFISA156MSFRBNY",
            "percent_reporting_decrease": "DTFDSA156MSFRBNY",
            "percent_reporting_no_change": "DTFNSA156MSFRBNY",
        },
        "not_sa": {
            "diffusion_index": "DTFDINA066MNFRBNY",
            "percent_reporting_increase": "DTFINA156MNFRBNY",
            "percent_reporting_decrease": "DTFDNA156MNFRBNY",
            "percent_reporting_no_change": "DTFNNA156MNFRBNY",
        },
    },
}

# Reverse lookups: FRED series id -> full topic key, and id -> field name.
# Built once from the catalog so the melt maps each series back to its row.
ID_TO_TOPIC: dict[str, str] = {}
ID_TO_FIELD: dict[str, str] = {}
for _key, _value in NY_MANUFACTURING_OUTLOOK.items():
    for _sub_key, _sub_value in _value.items():
        for _field_key, _series_id in _sub_value.items():
            ID_TO_TOPIC[_series_id] = _key
            ID_TO_FIELD[_series_id] = _field_key

# Stable ordering for the long rows (matches catalog insertion order).
TOPIC_ORDER = {topic: i for i, topic in enumerate(NY_MANUFACTURING_OUTLOOK)}

# Short topic selectors (the user picks these; the fetcher expands each to its
# current_ and future_ catalog entries). Ported verbatim from the blueprint.
NY_MANUFACTURING_OUTLOOK_CHOICES = [
    "business_outlook",
    "hours_worked",
    "employment",
    "inventories",
    "prices_received",
    "prices_paid",
    "capex",
    "unfilled_orders",
    "new_orders",
    "shipments",
    "delivery_times",
]

NyManufacturingOutlookChoices = Literal[
    "business_outlook",
    "hours_worked",
    "employment",
    "inventories",
    "prices_received",
    "prices_paid",
    "capex",
    "unfilled_orders",
    "new_orders",
    "shipments",
    "delivery_times",
]

# Per-field normalization. The percent_reporting_* fields carry
# x-frontend_multiply:100 in the standard model json_schema_extra -> stored as
# a fraction (value / 100). diffusion_index has no x-frontend_multiply -> as-is.
_PERCENT_FIELDS = {
    "percent_reporting_increase",
    "percent_reporting_decrease",
    "percent_reporting_no_change",
}


class SugraManufacturingOutlookNYQueryParams(ManufacturingOutlookTexasQueryParams):
    """Sugra Manufacturing Outlook - New York - Query Params."""

    __json_schema_extra__ = {
        "topic": {
            "multiple_items_allowed": True,
            "choices": NY_MANUFACTURING_OUTLOOK_CHOICES,
            "x-widget_config": {
                "value": "new_orders",
            },
        },
    }

    topic: NyManufacturingOutlookChoices | str = Field(
        default="new_orders",
        description="The topic for the survey response.",
    )
    seasonally_adjusted: bool = Field(
        default=False,
        description="Whether the data is seasonally adjusted, default is False.",
    )

    @field_validator("topic", mode="before", check_fields=False)
    @classmethod
    def validate_topic(cls, v):
        """Validate the topic(s), defaulting invalid/empty input to new_orders."""
        if v is None:
            return "new_orders"
        topics: list = []
        if isinstance(v, list):
            topics = v
        elif isinstance(v, str):
            topics = v.split(",")
        new_topics: list = []
        for t in topics:
            t = t.strip() if isinstance(t, str) else t
            if t in NY_MANUFACTURING_OUTLOOK_CHOICES:
                new_topics.append(t)
            else:
                warn(f"Invalid topic: {t}")
        if not new_topics:
            new_topics = ["new_orders"]
        return ",".join(new_topics)


class SugraManufacturingOutlookNYData(ManufacturingOutlookTexasData):
    """Sugra Manufacturing Outlook - New York - Data."""


class SugraManufacturingOutlookNYFetcher(
    Fetcher[
        SugraManufacturingOutlookNYQueryParams,
        list[SugraManufacturingOutlookNYData],
    ]
):
    """Fetch the Empire State (NY) Manufacturing Survey series from the Sugra API."""

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> SugraManufacturingOutlookNYQueryParams:
        """Transform the query parameters."""
        return SugraManufacturingOutlookNYQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: SugraManufacturingOutlookNYQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Fetch the FRED series for the selected topic(s) and seasonality."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import OpenBBError

        from openbb_sugra.utils.helpers import fred_series_payloads, get_api_key

        api_key = get_api_key(credentials)
        seasonality = "sa" if query.seasonally_adjusted is True else "not_sa"
        # A default call selects only "new_orders" -> current_ + future_ * 4
        # fields = 8 series. Selector-bounded; never a full 100+ series fan-out.
        ids: list[str] = []
        for t in query.topic.split(","):
            for prefix in ("future_", "current_"):
                ids.extend(
                    NY_MANUFACTURING_OUTLOOK.get(prefix + t, {})
                    .get(seasonality, {})
                    .values()
                )
        if not ids:
            raise OpenBBError(
                "No valid topic selected. Please select a valid topic."
            )
        return await fred_series_payloads(
            api_key, ids, start_date=query.start_date, end_date=query.end_date
        )

    @staticmethod
    def transform_data(
        query: SugraManufacturingOutlookNYQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[SugraManufacturingOutlookNYData]:
        """Melt the per-series payloads into long (date, topic) rows.

        Each row carries the four fields for one (date, topic). The
        percent_reporting_* fields carry x-frontend_multiply:100 -> stored as a
        fraction (value / 100); diffusion_index has no multiply -> kept as-is.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.errors import EmptyDataError

        from openbb_sugra.utils.helpers import fred_observations

        # (date, topic) -> assembled row.
        grouped: dict[tuple[str, str], dict] = {}
        for series_id, payload in (data or {}).items():
            topic = ID_TO_TOPIC.get(series_id)
            field = ID_TO_FIELD.get(series_id)
            if topic is None or field is None:
                continue
            is_percent = field in _PERCENT_FIELDS
            for obs in fred_observations(payload):
                date = obs["date"]
                value = obs["value"]
                # percent fields -> fraction (value / 100); diffusion -> as-is.
                value = value / 100 if is_percent else value
                row = grouped.setdefault(
                    (date, topic), {"date": date, "topic": topic}
                )
                row[field] = value

        if not grouped:
            raise EmptyDataError(
                "The request was returned empty. You may be experiencing rate"
                " limiting from the Sugra/FRED API. Please try again later and"
                " reduce the number of topics selected."
            )

        rows = sorted(
            grouped.values(),
            key=lambda r: (r["date"], TOPIC_ORDER.get(r["topic"], 99)),
        )
        return [SugraManufacturingOutlookNYData.model_validate(r) for r in rows]
