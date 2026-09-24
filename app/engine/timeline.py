from app.engine.log import DecisionEntry, DecisionLog
from app.engine.models import Event, Rule
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


def run(rules: list[Rule], events: list[Event]) -> DecisionLog:
    """Tier 1 run loop (spec §6.2). Pure function: same rules + events always
    produce the same log. No wall-clock reads, no RNG, no dict/set-iteration
    dependence — sort_events() fixes the only order-sensitive step.

    Position starts at "none" (the memo's own starting state) and updates from
    each fired rule's action, so requires_existing_position (the $195 stop is for
    existing holders only) is a real gate, not a label."""
    log = DecisionLog()
    tracker = ConsecutivePeriodTracker()
    fired_rule_ids: set[str] = set()
    position = "none"

    for event in sort_events(events):
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
