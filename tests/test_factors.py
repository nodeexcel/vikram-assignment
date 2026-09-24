from datetime import date

from app.engine.factors import factor_shift_proposals, respond_to_proposal
from app.engine.log import DecisionLog
from app.engine.loader import load_shared_factors
from app.engine.models import Event
from app.engine.timeline import run


def _factor_shift(factor_id, event_date=date(2027, 1, 28)):
    return Event(date=event_date, kind="factor_shift", ticker=None, payload={"factor_id": factor_id})


def test_sector_market_factor_shift_produces_one_proposal_per_exposure():
    factors = load_shared_factors()
    proposals = factor_shift_proposals(factors, _factor_shift("hyperscaler_capex_financing_shift"))
    tickers = {p.ticker for p in proposals}
    assert tickers == {"NVDA", "AMZN"}


def test_fan_out_sign_is_opposite_for_capex_financing_shift():
    factors = load_shared_factors()
    proposals = factor_shift_proposals(factors, _factor_shift("hyperscaler_capex_financing_shift"))
    direction = {p.ticker: p.action for p in proposals}
    assert direction["NVDA"] == "negative"
    assert direction["AMZN"] == "positive"


def test_fan_out_sign_is_same_for_ai_infrastructure_buildout():
    factors = load_shared_factors()
    proposals = factor_shift_proposals(factors, _factor_shift("ai_infrastructure_buildout"))
    direction = {p.ticker: p.action for p in proposals}
    assert direction["NVDA"] == "positive"
    assert direction["AMZN"] == "positive"


def test_internal_ring_factor_never_propagates():
    factors = load_shared_factors()
    proposals = factor_shift_proposals(factors, _factor_shift("share-ceded-to-custom-silicon"))
    assert proposals == []


def test_unknown_ring_factor_never_propagates():
    factors = load_shared_factors()
    proposals = factor_shift_proposals(factors, _factor_shift("guidance-bet"))
    assert proposals == []


def test_unrecognised_factor_id_produces_no_proposals():
    factors = load_shared_factors()
    proposals = factor_shift_proposals(factors, _factor_shift("does-not-exist"))
    assert proposals == []


def test_proposal_never_mutates_position_until_a_response_is_recorded():
    factors = load_shared_factors()
    event = _factor_shift("hyperscaler_capex_financing_shift")
    log = run(rules=[], events=[event], factors=factors)
    assert all(e.kind == "proposal" for e in log.entries)
    assert all(e.actor is None for e in log.entries)


def test_accept_and_reject_are_both_logged_with_the_actor():
    from app.engine.log import DecisionEntry

    log = DecisionLog()
    proposal = log.append(
        DecisionEntry(
            date=date(2027, 1, 28),
            event_kind="factor_shift",
            ticker="AMZN",
            kind="proposal",
            rule_id=None,
            factor_id="hyperscaler_capex_financing_shift",
            action="positive",
            reason="test proposal",
            source=None,
        )
    )

    accepted = respond_to_proposal(log, proposal.id, "accept", actor="user")
    assert accepted.kind == "proposal_response"
    assert accepted.action == "accept"
    assert accepted.actor == "user"
    assert accepted.responds_to == proposal.id

    log2 = DecisionLog()
    proposal2 = log2.append(
        DecisionEntry(
            date=date(2027, 1, 28),
            event_kind="factor_shift",
            ticker="NVDA",
            kind="proposal",
            rule_id=None,
            factor_id="hyperscaler_capex_financing_shift",
            action="negative",
            reason="test proposal",
            source=None,
        )
    )
    rejected = respond_to_proposal(log2, proposal2.id, "reject", actor="user")
    assert rejected.action == "reject"
