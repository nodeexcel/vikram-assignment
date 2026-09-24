from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.engine.loader import load_shared_factors, load_ticker_fixtures, load_timeline
from app.engine.timeline import initial_state_event, run

app = FastAPI(title="Lexo Trading Decision System")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

SCENARIOS = ["guide_holds", "capex_turns"]

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
    bundle = load_ticker_fixtures("NVDA")
    factors = load_shared_factors()
    checks = []
    for scenario in SCENARIOS:
        events = [initial_state_event(bundle.research), *load_timeline(scenario).events]
        hash_a = run(bundle.rules, events, bundle.overrides, factors).canonical_hash()
        hash_b = run(bundle.rules, events, bundle.overrides, factors).canonical_hash()
        checks.append({"scenario": scenario, "hash_a": hash_a, "hash_b": hash_b, "match": hash_a == hash_b})
    return templates.TemplateResponse(request, "determinism.html", {"checks": checks})
