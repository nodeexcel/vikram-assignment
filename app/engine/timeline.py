from app.engine.factors import factor_shift_proposals
from app.engine.log import DecisionEntry, DecisionLog
from app.engine.models import Event, Factor, Override, Research, Rule
from app.engine.rules import ConsecutivePeriodTracker, event_in_rule_window, single_event_satisfies

# Actions that change position state, read off the rule's own `action` string.
# "none" means no position; anything else (starter/full) counts as an existing
# position for requires_existing_position gating.
_POSITION_AFTER_ACTION = {
    "buy_full_weight": "full",
    "open_starter_position": "starter",
    "stop_exit": "none",
    "exit_short": "none",
    "sell": "none",
}


def sort_events(events: list[Event]) -> list[Event]:
    """Total order (date, kind, ticker) — no ties, so iteration order can never
    vary (spec §6.2). ticker sorts null-first via "" so cross-ticker events at the
    same (date, kind) still order deterministically."""
    return sorted(events, key=lambda e: (e.date, e.kind, e.ticker or ""))


def initial_state_event(research: Research) -> Event:
    """Standing research facts (spring_state) as a state_snapshot event at the
    research as-of date, so a continuous state-only rule (the platform default)
    fires through the same event-loop machinery as everything else (spec §6.4)."""
    return Event(
        date=research.as_of,
        kind="state_snapshot",
        ticker=research.ticker,
        payload={"spring_state": research.spring_state} if research.spring_state else {},
    )


def run(
    rules: list[Rule], events: list[Event], overrides: list[Override] = (), factors: list[Factor] = ()
) -> DecisionLog:
    """Tier 1 + Tier 2 run loop (spec §6.2, §6.5). Pure function: same rules +
    events + factors always produce the same log. No wall-clock reads, no RNG, no
    dict/set-iteration dependence — sort_events() fixes the only order-sensitive
    step.

    Position starts at "none" (the memo's own starting state) and updates from
    each fired rule's action, so requires_existing_position (the $195 stop is for
    existing holders only) is a real gate, not a label.

    A rule with a matching override (spec §6.4) never applies its action — the
    log records the override instead of a plain rule_fired, with what the rule
    would have done, what actually happened, and why.

    A factor_shift event logs a proposal per affected ticker (Tier 2, §6.5) and
    never touches position — a proposal only becomes real once a human response
    is recorded via factors.respond_to_proposal(), which this loop does not call."""
    override_by_rule_id = {o.rule_id: o for o in overrides}
    log = DecisionLog()
    tracker = ConsecutivePeriodTracker()
    fired_rule_ids: set[str] = set()
    position = "none"

    for event in sort_events(events):
        if event.kind == "factor_shift":
            for proposal in factor_shift_proposals(list(factors), event):
                log.append(proposal)
            continue

        for rule in rules:
            if rule.id in fired_rule_ids:
                continue
            if rule.requires_existing_position and position == "none":
                continue
            if rule.ticker is not None and event.ticker is not None and rule.ticker != event.ticker:
                continue
            if not event_in_rule_window(event, rule):
                continue

            single_ok = single_event_satisfies(rule.trigger, event.payload)
            if rule.trigger.consecutive_periods:
                key = (rule.id, event.ticker)
                fired = tracker.observe(key, single_ok, rule.trigger.consecutive_periods)
            else:
                fired = single_ok

            if fired:
                fired_rule_ids.add(rule.id)
                override = override_by_rule_id.get(rule.id)
                if override is not None:
                    # Overridden: the action never applies, so position does not
                    # change — that is the entire point of the override.
                    log.append(
                        DecisionEntry(
                            date=event.date,
                            event_kind=event.kind,
                            ticker=event.ticker,
                            kind="override",
                            rule_id=rule.id,
                            action=override.actual,
                            reason=override.reason,
                            source=override.source,
                            would_have_done=override.would_have_done,
                            actor=override.actor,
                        )
                    )
                else:
                    if rule.action in _POSITION_AFTER_ACTION:
                        position = _POSITION_AFTER_ACTION[rule.action]
                    log.append(
                        DecisionEntry(
                            date=event.date,
                            event_kind=event.kind,
                            ticker=event.ticker,
                            kind="rule_fired",
                            rule_id=rule.id,
                            action=rule.action,
                            reason=rule.name,
                            source=rule.source,
                        )
                    )

    return log
