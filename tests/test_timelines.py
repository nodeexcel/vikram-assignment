from datetime import date

import pytest

from app.engine.loader import load_timeline, load_ticker_fixtures
from app.engine.timeline import run


@pytest.fixture(scope="module")
def nvda_rules():
    return load_ticker_fixtures("NVDA").rules


def test_guide_holds_buys_then_stops_out(nvda_rules):
    """BUG-20260924-1822-41: the brief asks the system to decide whether to hold,
    how large, and when to stop. guide_holds must show all three, not just the
    buy — the stop is dormant until a position exists."""
    timeline = load_timeline("guide_holds")
    log = run(nvda_rules, timeline.events)
    assert [e.rule_id for e in log.entries] == [
        "reentry-buy-full-weight",
        "stop-195-two-consecutive-weekly-closes",
    ]


def test_guide_holds_survives_the_single_week_below_the_stop(nvda_rules):
    """The memo's stated reason for two-close confirmation: "so a single volatile
    week around an earnings print does not trigger the exit." guide_holds closes
    at 193.50 on 2027-01-15, recovers above the level the next week, and must not
    stop out until the genuine two-week streak completes on 2027-02-05."""
    timeline = load_timeline("guide_holds")
    log = run(nvda_rules, timeline.events)
    stop = next(e for e in log.entries if e.rule_id == "stop-195-two-consecutive-weekly-closes")
    assert stop.date == date(2027, 2, 5)

    closes_below = [e for e in timeline.events if e.payload.get("price_close", 999) <= 195.0]
    assert min(e.date for e in closes_below) == date(2027, 1, 15), (
        "fixture must still contain the earlier non-firing close, or this test proves nothing"
    )


def test_guide_holds_position_size_is_recorded_at_each_step(nvda_rules):
    """BUG-20260924-1822-42: size is a first-class output of the brief ("how
    large"), so every entry records the position it produced."""
    timeline = load_timeline("guide_holds")
    log = run(nvda_rules, timeline.events)
    assert [(e.rule_id, e.position_after) for e in log.entries] == [
        ("reentry-buy-full-weight", "full"),
        ("stop-195-two-consecutive-weekly-closes", "none"),
    ]


def test_capex_turns_fires_base_row_then_exit_short(nvda_rules):
    timeline = load_timeline("capex_turns")
    log = run(nvda_rules, timeline.events)
    fired = [e.rule_id for e in log.entries]
    assert fired == ["base-row-neither-confirms-nor-breaks", "exit-short-hyperscaler-capex"]


def test_capex_turns_stop_does_not_fire_despite_two_consecutive_closes_below_195(nvda_rules):
    # Non-price divergent future, but the price path is authored to cross $195.00
    # on two consecutive weekly closes too — and correctly does NOT stop out,
    # because no position was ever opened (the stop is existing-holders-only).
    timeline = load_timeline("capex_turns")
    log = run(nvda_rules, timeline.events)
    assert "stop-195-two-consecutive-weekly-closes" not in [e.rule_id for e in log.entries]


def test_each_timeline_diverges_on_a_disclosure_not_a_price(nvda_rules):
    """The brief asks for divergent futures where at least one turns on something
    that is not a price. The event that SETS each scenario's path must therefore be
    a disclosure. A price-driven stop may follow afterwards — a stop is risk
    management on an already-chosen path, not the thing the future turns on.

    This replaces an earlier assertion that no fired entry was price-driven. That
    held only because the stop never fired in either scenario, which was
    BUG-20260924-1822-41 — the test was encoding the gap as the specification."""
    for name in ("guide_holds", "capex_turns"):
        log = run(nvda_rules, load_timeline(name).events)
        assert log.entries, f"{name} fired nothing"
        assert log.entries[0].event_kind in {"guidance", "third_party_guidance"}, (
            f"{name} diverges on {log.entries[0].event_kind}, not a disclosure"
        )


def test_capex_turns_turns_on_a_third_party_disclosure(nvda_rules):
    """"At least one must turn on something that is not a price: a disclosure, a
    guidance change, a third-party event." capex_turns exits on four OTHER
    companies' capex guidance — not the issuer's own, and not a price."""
    log = run(nvda_rules, load_timeline("capex_turns").events)
    exit_entry = next(e for e in log.entries if e.rule_id == "exit-short-hyperscaler-capex")
    assert exit_entry.event_kind == "third_party_guidance"


def test_the_stop_is_the_only_price_driven_decision(nvda_rules):
    """Preserves the intent of the assertion this replaced: price may not drive any
    decision except the one rule the memo defines on a price level."""
    for name in ("guide_holds", "capex_turns"):
        log = run(nvda_rules, load_timeline(name).events)
        price_driven = [e for e in log.entries if e.event_kind == "price_close"]
        assert all(e.rule_id == "stop-195-two-consecutive-weekly-closes" for e in price_driven), (
            f"{name} has a non-stop decision driven by a price"
        )
