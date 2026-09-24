from app.engine.models import Event, Rule, Trigger

_COMPARATORS = {
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
}


class ConsecutivePeriodTracker:
    """Shared consecutive-period confirmation primitive (spec §6.3). The $195 stop
    (two consecutive weekly closes) and, in principle, any other trigger needing the
    same confirmation use this rather than a bespoke counter each. Counts a streak of
    qualifying observations per key; fires once, the first time the streak reaches n.
    A non-qualifying observation breaks the streak and clears the fired flag, so a
    later streak can fire again."""

    def __init__(self) -> None:
        self._streaks: dict[tuple, int] = {}
        self._fired: set[tuple] = set()

    def observe(self, key: tuple, qualifies: bool, n: int) -> bool:
        if not qualifies:
            self._streaks[key] = 0
            self._fired.discard(key)
            return False
        streak = self._streaks.get(key, 0) + 1
        self._streaks[key] = streak
        if streak >= n and key not in self._fired:
            self._fired.add(key)
            return True
        return False


def single_event_satisfies(trigger: Trigger, payload: dict) -> bool:
    """Does this one event's payload satisfy the trigger, ignoring any
    consecutive-period requirement (that is tracked separately, across events, by
    ConsecutivePeriodTracker)."""
    if trigger.metric not in payload:
        return False
    value = payload[trigger.metric]

    if trigger.comparator == "eq":
        if value != trigger.threshold:
            return False
    else:
        if not isinstance(value, (int, float)) or not isinstance(trigger.threshold, (int, float)):
            return False
        if not _COMPARATORS[trigger.comparator](value, trigger.threshold):
            return False
        if trigger.upper_threshold is not None and not (value < trigger.upper_threshold):
            return False

    if trigger.requires_backlog_detail and not payload.get("backlog_detail"):
        return False

    return True


def event_in_rule_window(event: Event, rule: Rule) -> bool:
    """Does this event fall in the rule's date applicability?
    - event_date set: exact-date rules (the 2026-11-17 commentary rules, the formal
      Sell date).
    - trigger.window_start/end set: ranged rules (the hyperscaler exit window).
    - neither set: continuous rules (the $195 stop, the platform default)."""
    if rule.event_date is not None:
        return event.date == rule.event_date
    trigger = rule.trigger
    if trigger.window_start is not None and event.date < trigger.window_start:
        return False
    if trigger.window_end is not None and event.date > trigger.window_end:
        return False
    return True
