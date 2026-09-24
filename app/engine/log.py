import hashlib
import json
from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.engine.models import Source


class DecisionEntry(BaseModel):
    """One append-only row in the decision log. `date` is the in-world event date —
    never a wall-clock execution timestamp (spec §7 determinism requires this)."""

    date: date
    event_kind: str
    ticker: str | None
    kind: Literal["rule_fired", "kill_switch_triggered", "override", "proposal", "proposal_response"]
    rule_id: str | None
    action: str | None
    reason: str
    source: Source | None


class DecisionLog(BaseModel):
    entries: list[DecisionEntry] = []

    def append(self, entry: DecisionEntry) -> None:
        self.entries.append(entry)

    def canonical_bytes(self) -> bytes:
        """Sorted keys, fixed float formatting, in-world dates only. §7."""
        data = self.model_dump(mode="json")
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def canonical_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
