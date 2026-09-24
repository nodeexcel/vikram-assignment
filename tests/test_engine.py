from datetime import date

import pytest

from app.engine.loader import load_ticker_fixtures
from app.engine.models import Event
from app.engine.rules import ConsecutivePeriodTracker
from app.engine.timeline import run


@pytest.fixture(scope="module")
def nvda_rules():
    return load_ticker_fixtures("NVDA").rules


def _guidance_event(pct, backlog_detail=False, event_date=date(2026, 11, 17)):
    return Event(
        date=event_date,
        kind="guidance",
        ticker="NVDA",
        payload={"fy2028_commentary_pct": pct, "backlog_detail": backlog_detail},
    )


def test_buy_fires_at_exactly_70_with_backlog_detail(nvda_rules):
    log = run(nvda_rules, [_guidance_event(70, backlog_detail=True)])
    assert [e.rule_id for e in log.entries] == ["reentry-buy-full-weight"]


def test_buy_does_not_fire_at_69_9(nvda_rules):
    log = run(nvda_rules, [_guidance_event(69.9, backlog_detail=True)])
    assert "reentry-buy-full-weight" not in [e.rule_id for e in log.entries]


def test_buy_requires_backlog_detail(nvda_rules):
    # The memo's three rows don't define a ">=70% without backlog detail" case —
    # not firing anything here is correct, not a gap: -09's timelines only author
    # the three paths the source actually describes.
    log = run(nvda_rules, [_guidance_event(72, backlog_detail=False)])
    assert "reentry-buy-full-weight" not in [e.rule_id for e in log.entries]


def test_bear_row_fires_below_45_not_at_45(nvda_rules):
    log = run(nvda_rules, [_guidance_event(44.9)])
    assert "bear-row-guidance-below-45" in [e.rule_id for e in log.entries]

    log = run(nvda_rules, [_guidance_event(45)])
    assert "bear-row-guidance-below-45" not in [e.rule_id for e in log.entries]


def test_base_row_covers_the_45_to_70_gap_without_overlapping_buy(nvda_rules):
    # BUG-20260924-1421-20: 72% with backlog detail must fire buy, not base-row too.
    log = run(nvda_rules, [_guidance_event(72, backlog_detail=True)])
    fired = [e.rule_id for e in log.entries]
    assert fired == ["reentry-buy-full-weight"]

    log = run(nvda_rules, [_guidance_event(50)])
    assert [e.rule_id for e in log.entries] == ["base-row-neither-confirms-nor-breaks"]


def test_exit_short_fires_inside_window_not_outside(nvda_rules):
    inside = Event(
        date=date(2027, 1, 30),
        kind="third_party_guidance",
        ticker="NVDA",
        payload={"hyperscaler_capex_flat_or_down_count": 2},
    )
    log = run(nvda_rules, [inside])
    assert "exit-short-hyperscaler-capex" in [e.rule_id for e in log.entries]

    outside = Event(
        date=date(2027, 3, 1),
        kind="third_party_guidance",
        ticker="NVDA",
        payload={"hyperscaler_capex_flat_or_down_count": 2},
    )
    log = run(nvda_rules, [outside])
    assert "exit-short-hyperscaler-capex" not in [e.rule_id for e in log.entries]


def test_exit_short_needs_at_least_two_hyperscalers(nvda_rules):
    event = Event(
        date=date(2027, 1, 30),
        kind="third_party_guidance",
        ticker="NVDA",
        payload={"hyperscaler_capex_flat_or_down_count": 1},
    )
    log = run(nvda_rules, [event])
    assert "exit-short-hyperscaler-capex" not in [e.rule_id for e in log.entries]


def test_stop_does_not_fire_with_no_position(nvda_rules):
    events = [
        Event(date=date(2026, 10, 5), kind="price_close", ticker="NVDA", payload={"price_close": 190}),
        Event(date=date(2026, 10, 12), kind="price_close", ticker="NVDA", payload={"price_close": 185}),
    ]
    log = run(nvda_rules, events)
    assert "stop-195-two-consecutive-weekly-closes" not in [e.rule_id for e in log.entries]


def test_stop_fires_after_position_opened_and_two_consecutive_closes_below(nvda_rules):
    events = [
        _guidance_event(70, backlog_detail=True, event_date=date(2026, 11, 17)),  # opens position (full)
        Event(date=date(2026, 11, 20), kind="price_close", ticker="NVDA", payload={"price_close": 190}),
        Event(date=date(2026, 11, 27), kind="price_close", ticker="NVDA", payload={"price_close": 188}),
    ]
    log = run(nvda_rules, events)
    fired = [e.rule_id for e in log.entries]
    assert "stop-195-two-consecutive-weekly-closes" in fired


def test_stop_does_not_fire_on_one_close_below_195(nvda_rules):
    events = [
        _guidance_event(70, backlog_detail=True, event_date=date(2026, 11, 17)),
        Event(date=date(2026, 11, 20), kind="price_close", ticker="NVDA", payload={"price_close": 190}),
    ]
    log = run(nvda_rules, events)
    assert "stop-195-two-consecutive-weekly-closes" not in [e.rule_id for e in log.entries]


def test_stop_requires_consecutive_closes_not_just_two_total(nvda_rules):
    events = [
        _guidance_event(70, backlog_detail=True, event_date=date(2026, 11, 17)),
        Event(date=date(2026, 11, 20), kind="price_close", ticker="NVDA", payload={"price_close": 190}),
        Event(date=date(2026, 11, 27), kind="price_close", ticker="NVDA", payload={"price_close": 200}),  # breaks streak
        Event(date=date(2026, 12, 4), kind="price_close", ticker="NVDA", payload={"price_close": 190}),
    ]
    log = run(nvda_rules, events)
    assert "stop-195-two-consecutive-weekly-closes" not in [e.rule_id for e in log.entries]


def test_consecutive_period_tracker_resets_on_non_qualifying_observation():
    tracker = ConsecutivePeriodTracker()
    key = ("x", "NVDA")
    assert tracker.observe(key, True, 2) is False
    assert tracker.observe(key, False, 2) is False
    assert tracker.observe(key, True, 2) is False
    assert tracker.observe(key, True, 2) is True


def test_run_is_deterministic_regardless_of_event_input_order(nvda_rules):
    events = [
        _guidance_event(70, backlog_detail=True, event_date=date(2026, 11, 17)),
        Event(date=date(2026, 11, 20), kind="price_close", ticker="NVDA", payload={"price_close": 190}),
        Event(date=date(2026, 11, 27), kind="price_close", ticker="NVDA", payload={"price_close": 188}),
    ]
    log_forward = run(nvda_rules, events)
    log_reversed = run(nvda_rules, list(reversed(events)))
    assert log_forward.canonical_hash() == log_reversed.canonical_hash()
