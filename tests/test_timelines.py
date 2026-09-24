import pytest

from app.engine.loader import load_timeline, load_ticker_fixtures
from app.engine.timeline import run


@pytest.fixture(scope="module")
def nvda_rules():
    return load_ticker_fixtures("NVDA").rules


def test_guide_holds_fires_reentry_buy_and_nothing_else(nvda_rules):
    timeline = load_timeline("guide_holds")
    log = run(nvda_rules, timeline.events)
    assert [e.rule_id for e in log.entries] == ["reentry-buy-full-weight"]


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


def test_both_timelines_are_disclosure_driven_not_price_driven(nvda_rules):
    for name in ("guide_holds", "capex_turns"):
        timeline = load_timeline(name)
        log = run(nvda_rules, timeline.events)
        fired_kinds = {e.event_kind for e in log.entries}
        assert fired_kinds <= {"guidance", "third_party_guidance"}
