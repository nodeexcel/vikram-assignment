from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Doc = Literal["NVDA-memo", "NVDA-theme", "NVDA-factor", "AMZN-memo", "AMZN-theme", "AMZN-factor"]
Ticker = Literal["NVDA", "AMZN"]


class ProvenanceStatus(StrEnum):
    DERIVED = "derived"
    PARTIAL = "partial"
    ADDED = "added"


class Source(BaseModel):
    doc: Doc
    page: int = Field(gt=0)
    quote: str = Field(min_length=1)


class Sourced(BaseModel):
    """Every claim in the system carries provenance. See spec §5.2-5.4."""

    source: Source | None = None
    provenance_status: ProvenanceStatus
    gap_note: str | None = None
    rationale: str | None = None

    @model_validator(mode="after")
    def _check_provenance(self) -> "Sourced":
        if self.provenance_status in (ProvenanceStatus.DERIVED, ProvenanceStatus.PARTIAL):
            if self.source is None:
                raise ValueError(f"provenance_status={self.provenance_status} requires a source")
        if self.provenance_status == ProvenanceStatus.PARTIAL and not self.gap_note:
            raise ValueError("provenance_status=partial requires gap_note quoting the source's own admission")
        if self.provenance_status == ProvenanceStatus.ADDED:
            if not self.rationale:
                raise ValueError("provenance_status=added requires rationale")
            if self.source is not None:
                raise ValueError("provenance_status=added must not carry a source — it is not in the source")
        return self


class Trigger(BaseModel):
    metric: str
    comparator: Literal["gte", "lte", "gt", "lt", "eq"]
    threshold: float
    window: str | None = None
    consecutive_periods: int | None = Field(default=None, gt=0)


class Rule(Sourced):
    id: str
    name: str
    ticker: Ticker | None = None
    applies_when: str | None = None
    trigger: Trigger
    action: str
    event_date: date | None = None


class Override(Sourced):
    id: str
    rule_id: str
    would_have_done: str
    actual: str
    reason: str
    actor: Literal["memo", "user"]


class KillSwitch(Sourced):
    id: str
    name: str
    metric: str
    threshold: str
    cadence: str
    watch_period: str
    consecutive_periods: int | None = Field(default=None, gt=0)


class Exposure(Sourced):
    """One ticker's stake in a shared factor. local_id/local_name preserve that
    ticker's own memo's numbering and wording verbatim — the two memos name and
    number the same force differently, and the interface shows the source's words,
    not ours."""

    local_id: int | str
    local_name: str
    direction: Literal["positive", "negative"]
    impact: float = Field(ge=0, le=1)
    weight: int | None = Field(default=None, ge=0, le=100)


class Factor(BaseModel):
    """Shared, ticker-agnostic state (spec §6.5). Identity, ring and force are
    recorded once; direction/impact/weight/provenance are per ticker under
    exposures, because the same force can be bearish for one holding and bullish
    for another."""

    id: str
    ring: Literal["internal", "sector", "market"]
    force: Literal["wind", "wave", "mud"]
    label: str
    exposures: dict[Ticker, Exposure]

    @model_validator(mode="after")
    def _check_exposure_rules(self) -> "Factor":
        if not self.exposures:
            raise ValueError(f"factor {self.id}: must have at least one exposure")
        if self.ring == "internal" and len(self.exposures) > 1:
            raise ValueError(
                f"factor {self.id}: internal-ring factors cannot propagate, so a multi-ticker "
                f"exposure ({sorted(self.exposures)}) is a category mistake — see spec §6.5"
            )
        return self


class ScenarioLeg(Sourced):
    label: Literal["bull", "base", "bear"]
    probability: float = Field(ge=0, le=1)
    price: float
    return_pct: float


class ScenarioSet(BaseModel):
    horizon: Literal["intrinsic_3_5yr", "tactical_12mo"]
    legs: list[ScenarioLeg]
    weighted_price: float
    weighted_return_pct: float


class Research(Sourced):
    ticker: Ticker
    as_of: date
    reference_price: float = Field(gt=0)
    stance: str
    conviction: str
    position: str
    horizon: str
    spring_state: str | None = None


class FixtureBundle(BaseModel):
    ticker: Ticker
    research: Research
    scenarios: list[ScenarioSet]
    rules: list[Rule]
    overrides: list[Override] = []
    kill_switches: list[KillSwitch] = []
