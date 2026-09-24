from typing import Literal

from app.engine.log import DecisionEntry, DecisionLog
from app.engine.models import Event, Factor


def factor_shift_proposals(factors: list[Factor], event: Event) -> list[DecisionEntry]:
    """Tier 2 (spec §6.5). A factor_shift event on a sector- or market-ring factor
    proposes a re-rate for every ticker in that factor's exposures — read off the
    ring assignment, never inferred from name. Internal and unknown-ring factors
    never propagate (BUG-20260924-1421-18: that boundary is load-bearing).

    Returns unappended entries — the caller decides whether/when to log them,
    e.g. from within timeline.run()."""
    factor_id = event.payload.get("factor_id")
    factor = next((f for f in factors if f.id == factor_id), None)
    if factor is None or factor.ring not in ("sector", "market"):
        return []

    proposals = []
    for ticker, exposure in factor.exposures.items():
        proposals.append(
            DecisionEntry(
                date=event.date,
                event_kind=event.kind,
                ticker=ticker,
                kind="proposal",
                rule_id=None,
                factor_id=factor.id,
                action=exposure.direction,
                reason=(
                    f"{factor.label}: re-rated {exposure.direction} for {ticker} "
                    f"(source's own local name: {exposure.local_name!r})"
                ),
                source=exposure.source,
            )
        )
    return proposals


def respond_to_proposal(
    log: DecisionLog, proposal_id: int, decision: Literal["accept", "reject"], actor: str = "user"
) -> DecisionEntry:
    """Record a human's response to a proposal. Both accept and reject are logged
    with the actor — a proposal never mutates a position on its own (ADR
    constraint); only a logged human decision does, and this is where the log
    records it, not the proposal itself."""
    proposal = next(e for e in log.entries if e.id == proposal_id and e.kind == "proposal")
    return log.append(
        DecisionEntry(
            date=proposal.date,
            event_kind=proposal.event_kind,
            ticker=proposal.ticker,
            kind="proposal_response",
            rule_id=None,
            factor_id=proposal.factor_id,
            responds_to=proposal.id,
            action=decision,
            reason=f"{actor} {decision}ed the proposal to re-rate {proposal.ticker} {proposal.action}",
            source=None,
            actor=actor,
        )
    )
