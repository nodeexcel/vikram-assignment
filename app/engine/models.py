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
    # str threshold is for categorical metrics compared with eq (e.g.
    # spring_state == "Neutral"); gte/lte/gt/lt only make sense against a float.
    threshold: float | str
    # Upper bound for a closed range: threshold <= metric < upper_threshold. Unset
    # means the comparator alone decides (open-ended). BUG-20: without this, two
    # single-sided rules over the same metric can silently overlap.
    upper_threshold: float | None = None
    window_start: date | None = None
    window_end: date | None = None
    consecutive_periods: int | None = Field(default=None, gt=0)
    # BUG-21: a bare count is ambiguous (2 daily closes != 2 weekly closes).
    period_unit: Literal["daily", "weekly", "monthly", "quarterly"] | None = None
    # ISS-23: was folded into the metric name (..._with_backlog_detail); now a
    # separate, explicit condition so every 2026-11-17 rule reads the same metric.
    requires_backlog_detail: bool = False

    @model_validator(mode="after")
    def _check_consecutive_periods_has_unit(self) -> "Trigger":
        if self.consecutive_periods is not None and self.period_unit is None:
            raise ValueError("consecutive_periods requires period_unit — a bare count is ambiguous (BUG-20260924-1421-21)")
        if self.comparator != "eq" and isinstance(self.threshold, str):
            raise ValueError(f"comparator={self.comparator!r} against a string threshold is not orderable — only eq may compare strings")
        return self


class Rule(Sourced):
    id: str
    name: str
    ticker: Ticker | None = None
    # ISS-22: was a free-text string ("position != none") the engine can't
    # evaluate. The only real precondition in this source is "existing holders
    # only" (the $195 stop), so this is the one structured flag needed for it.
    requires_existing_position: bool = False
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
    # Impact (0-1) is a Light Cone diagram attribute. The theme report's promoted-
    # factor descriptions give weight but not impact for several factors — left
    # unset rather than guessed, per "derived, not invented".
    impact: float | None = Field(default=None, ge=0, le=1)
    weight: int | None = Field(default=None, ge=0, le=100)


class Factor(BaseModel):
    """Shared, ticker-agnostic state (spec §6.5). Identity, ring and force are
    recorded once; direction/impact/weight/provenance are per ticker under
    exposures, because the same force can be bearish for one holding and bullish
    for another."""

    id: str
    # BUG-20260924-1421-18: ring must come from the Light Cone diagram only — never
    # inferred from the theme report's composition "zone" (intrinsic/ecosystem/
    # external is a controllability split over the 8 weighted factors; Light Cone's
    # internal/sector/market is a propagation-scope split over all 28, and they
    # come apart for real factors, e.g. fc_01 is zone=external but Light Cone #5
    # internal). "unknown" means no confident Light Cone entry was found for this
    # promoted factor — it is excluded from propagation exactly like internal.
    ring: Literal["internal", "sector", "market", "unknown"]
    # Force type is a Light Cone (28-factor diagram) attribute. The memo and theme
    # report do not state it for several of the 8 promoted/weighted factors — left
    # unset rather than guessed for those, per "derived, not invented".
    force: Literal["wind", "wave", "mud"] | None = None
    label: str
    exposures: dict[Ticker, Exposure]

    @model_validator(mode="after")
    def _check_exposure_rules(self) -> "Factor":
        if not self.exposures:
            raise ValueError(f"factor {self.id}: must have at least one exposure")
        if self.ring in ("internal", "unknown") and len(self.exposures) > 1:
            raise ValueError(
                f"factor {self.id}: {self.ring}-ring factors cannot propagate, so a multi-ticker "
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
    # The 12-month tactical table's weighted row carries no price, only a return —
    # the memo prints "-" for that cell.
    weighted_price: float | None = None
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


class Event(BaseModel):
    """A dated input to the engine run (spec §6.1). Scenario-timeline data, not a
    'claim' in the provenance sense — no fail-fast source requirement here."""

    date: date
    kind: Literal["disclosure", "guidance", "third_party_guidance", "price_close", "factor_shift"]
    ticker: Ticker | None = None
    payload: dict = Field(default_factory=dict)
    source: Source | None = None


class Timeline(BaseModel):
    """A scenario's authored sequence of events (spec §8/§9). Not a claim — the
    two futures are constructed, dated projections, not sourced facts; individual
    events may still carry a source where they restate a dated trigger the memo
    itself states (e.g. the 2026-11-17 print date)."""

    name: str
    description: str
    events: list[Event]


class FixtureBundle(BaseModel):
    ticker: Ticker
    research: Research
    scenarios: list[ScenarioSet]
    rules: list[Rule]
    overrides: list[Override] = []
    kill_switches: list[KillSwitch] = []
