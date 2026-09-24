import hashlib
import json
from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.engine.models import Source


class DecisionEntry(BaseModel):
    """One append-only row in the decision log. `date` is the in-world event date —
    never a wall-clock execution timestamp (spec §7 determinism requires this).
    `id` is assigned by DecisionLog.append() in append order, so a
    proposal_response can reference the proposal it answers."""

    id: int = 0
    date: date
    event_kind: str
    ticker: str | None
    kind: Literal["rule_fired", "kill_switch_triggered", "override", "proposal", "proposal_response"]
    rule_id: str | None
    action: str | None
    reason: str
    source: Source | None
    # Position held after this entry: "none" | "starter" | "full". The brief asks
    # the system to decide "whether to hold a position, how large, and when to
    # stop" — size is a first-class output, so it is recorded per entry rather
    # than left for a reader to infer from the action. On an override this shows
    # the position the override preserved, which is the point of the override.
    position_after: str | None = None
    # Only meaningful on kind="override": what the rule would have done, versus
    # what actually happened once the override suppressed it.
    would_have_done: str | None = None
    # Who made this call: "memo" (a source override), "user" (a human proposal
    # response), or None for an engine-only rule_fired.
    actor: Literal["memo", "user"] | None = None
    # Only meaningful on kind="proposal_response": which proposal this answers.
    responds_to: int | None = None
    factor_id: str | None = None


class DecisionLog(BaseModel):
    entries: list[DecisionEntry] = []

    def append(self, entry: DecisionEntry) -> DecisionEntry:
        entry.id = len(self.entries)
        self.entries.append(entry)
        return entry

    def canonical_bytes(self) -> bytes:
        """Sorted keys, fixed float formatting, in-world dates only. §7."""
        data = self.model_dump(mode="json")
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def canonical_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
