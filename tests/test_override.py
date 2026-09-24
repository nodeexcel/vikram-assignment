from app.engine.loader import load_ticker_fixtures
from app.engine.timeline import initial_state_event, run


def test_platform_rule_fires_and_is_overridden():
    bundle = load_ticker_fixtures("NVDA")
    events = [initial_state_event(bundle.research)]
    log = run(bundle.rules, events, bundle.overrides)

    entries = [e for e in log.entries if e.rule_id == "platform-neutral-spring-starter-position"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry.kind == "override"
    assert entry.action == "No new weight initiated"
    assert entry.would_have_done == "Open a starter position (roughly one-third weight)"
    assert "against the analysis the rule exists to serve" in entry.reason


def test_override_does_not_open_a_position():
    bundle = load_ticker_fixtures("NVDA")
    events = [
        initial_state_event(bundle.research),
        # Existing-holder-only stop should still not fire, since the override
        # means no position was actually opened.
    ]
    log = run(bundle.rules, events, bundle.overrides)
    assert not any(e.rule_id == "stop-195-two-consecutive-weekly-closes" for e in log.entries)


def test_without_overrides_platform_rule_fires_plainly():
    # Sanity: the suppression is the override's doing, not something baked into
    # the platform rule itself.
    bundle = load_ticker_fixtures("NVDA")
    events = [initial_state_event(bundle.research)]
    log = run(bundle.rules, events, overrides=())

    entries = [e for e in log.entries if e.rule_id == "platform-neutral-spring-starter-position"]
    assert len(entries) == 1
    assert entries[0].kind == "rule_fired"
    assert entries[0].action == "open_starter_position"
