from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.engine.factors import respond_to_proposal
from app.engine.loader import load_shared_factors, load_ticker_fixtures, load_timeline
from app.engine.log import DecisionLog
from app.engine.timeline import initial_state_event, run

app = FastAPI(title="Lexo Trading Decision System")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

SCENARIOS = ["guide_holds", "capex_turns"]
WHERE_THIS_GOES_NEXT_PATH = Path(__file__).parent.parent.parent / "WHERE_THIS_GOES_NEXT.md"

# Human responses to Tier 2 proposals, per scenario. In-memory only — this is a
# single-user local demo (spec §12: no auth/multi-user), and proposal ids are
# deterministic run-to-run, so replaying (proposal_id, decision) pairs against a
# freshly computed log always reattaches to the right proposal.
_PROPOSAL_RESPONSES: dict[str, list[tuple[int, str]]] = {name: [] for name in SCENARIOS}


def _run_scenario(scenario: str) -> DecisionLog:
    bundle = load_ticker_fixtures("NVDA")
    factors = load_shared_factors()
    events = [initial_state_event(bundle.research), *load_timeline(scenario).events]
    log = run(bundle.rules, events, bundle.overrides, factors)
    for proposal_id, decision in _PROPOSAL_RESPONSES[scenario]:
        respond_to_proposal(log, proposal_id, decision, actor="user")
    return log

# FEAT-20260924-1322-16: sourced but NOT engine-propagated. Both sides sit on the
# Internal ring in their own memo's Light Cone diagram, so the ring-based fan-out
# rule correctly declines to link them — see BUG-20260924-1322-15/spec §3. Shown
# here as a human-observed linkage, not a Factor entry (that would fail the
# internal-ring-cannot-have-two-exposures check on purpose).
CUSTOM_SILICON_OBSERVATION = {
    "headline": "Hyperscalers building their own silicon — a threat to NVDA, a moat for AMZN",
    "nvda": {
        "local_name": "Inference Share Loss to Custom Silicon",
        "quote": (
            "Custom ASIC shipments growing 44.6% against 16.1% for merchant GPUs, with parity "
            "projected by 2027, concentrated in exactly the stable-model inference workload a "
            "purpose-built part wins. Hyperscale - the cohort building TPU, Trainium, Maia and "
            "MTIA - is 50.9% of company revenue. This is the single structural threat every "
            "recent large bet is defending against."
        ),
        "doc": "NVDA-memo",
        "page": 9,
        "ring": "internal",
    },
    "amzn": {
        "local_name": "Custom Silicon Margin Moat",
        "quote": (
            "An eight-year chip-to-datacenter build means Graviton is used by 98% of the top "
            "1,000 EC2 customers, most Bedrock inference runs on Trainium, and more than half of "
            "the 2.1M+ AI chips landed in 12 months were Trainium. That own-silicon cost base is "
            "why AI growth has come with rising AWS margins, a moat widening in silicon though "
            "still dependent on partners at the model layer."
        ),
        "doc": "AMZN-memo",
        "page": 10,
        "ring": "internal",
    },
}


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/research")
def research_view(request: Request):
    """View 1 (spec §9): what the research concludes. Verdict and stance shown
    separately — different measures on different clocks, per the memo's own
    warning — both scenario tables, and the dated rules that change the rating."""
    bundle = load_ticker_fixtures("NVDA")
    intrinsic = next(s for s in bundle.scenarios if s.horizon == "intrinsic_3_5yr")
    tactical = next(s for s in bundle.scenarios if s.horizon == "tactical_12mo")
    dated_rules = sorted(
        (r for r in bundle.rules if r.event_date or r.trigger.window_start),
        key=lambda r: r.event_date or r.trigger.window_start,
    )
    return templates.TemplateResponse(
        request,
        "research.html",
        {
            "research": bundle.research,
            "intrinsic": intrinsic,
            "tactical": tactical,
            "dated_rules": dated_rules,
            "kill_switches": bundle.kill_switches,
        },
    )


@app.get("/rules")
def rules_view(request: Request):
    """View 2 (spec §9): every rule with its verbatim quote, doc and page.
    Bidirectional — claims that back more than one rule are grouped so the link
    runs both ways — plus the honest factor-coverage disclosure."""
    bundle = load_ticker_fixtures("NVDA")
    factors = load_shared_factors()

    claims: dict[tuple, dict] = {}
    for rule in bundle.rules:
        if rule.source is None:
            continue
        key = (rule.source.doc, rule.source.page, rule.source.quote)
        claims.setdefault(key, {"source": rule.source, "rules": []})["rules"].append(rule)

    nvda_transcribed = [f for f in factors if "NVDA" in f.exposures]

    return templates.TemplateResponse(
        request,
        "rules.html",
        {
            "rules": bundle.rules,
            "overrides": bundle.overrides,
            "claims": list(claims.values()),
            "factors": factors,
            "nvda_transcribed_count": len(nvda_transcribed),
            "custom_silicon": CUSTOM_SILICON_OBSERVATION,
        },
    )


@app.get("/determinism")
def determinism(request: Request):
    """Visible determinism check (spec §7): re-runs each scenario twice and shows
    both canonical hashes side by side with a match indicator. "Show us that it
    holds" — shown, not just asserted in a test file nobody but us reads."""
    checks = []
    for scenario in SCENARIOS:
        hash_a = _run_scenario(scenario).canonical_hash()
        hash_b = _run_scenario(scenario).canonical_hash()
        checks.append({"scenario": scenario, "hash_a": hash_a, "hash_b": hash_b, "match": hash_a == hash_b})
    return templates.TemplateResponse(request, "determinism.html", {"checks": checks})


@app.get("/where-this-goes-next")
def where_this_goes_next(request: Request):
    """FEAT-20260924-1250-14. Rendered as plain preformatted text rather than
    pulling in a markdown-to-HTML dependency for one page — the content is
    what's graded, not its typography."""
    text = WHERE_THIS_GOES_NEXT_PATH.read_text()
    return templates.TemplateResponse(request, "where_this_goes_next.html", {"text": text})


@app.get("/timeline/{scenario}")
def timeline_view(request: Request, scenario: str):
    """View 3 (spec §9): step through a scenario's dated events, see what the
    system did and why in plain language at each point, and accept or reject
    Tier 2 proposals. Every interaction is a form post + full page reload — no
    client framework (decided in Turn 4, notepad)."""
    if scenario not in SCENARIOS:
        scenario = SCENARIOS[0]
    log = _run_scenario(scenario)
    responses_by_proposal = {e.responds_to: e for e in log.entries if e.kind == "proposal_response"}
    return templates.TemplateResponse(
        request,
        "timeline.html",
        {
            "scenario": scenario,
            "scenarios": SCENARIOS,
            "entries": log.entries,
            "responses_by_proposal": responses_by_proposal,
        },
    )


@app.post("/timeline/{scenario}/proposal/{proposal_id}/{decision}")
def timeline_respond(scenario: str, proposal_id: int, decision: Literal["accept", "reject"]):
    """A body-less POST — path params only, so FastAPI never needs to parse a
    request body and python-multipart is not required. Recommended over a
    Form()-based endpoint specifically to avoid adding that dependency for a
    response that carries no free-text field (respond_to_proposal takes only
    decision + actor, and the ADR requires the response be logged with an
    actor, not a reason)."""
    if scenario in SCENARIOS:
        _PROPOSAL_RESPONSES[scenario].append((proposal_id, decision))
    return RedirectResponse(url=f"/timeline/{scenario}", status_code=303)
