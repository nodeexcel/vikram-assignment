import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from app.engine.factors import respond_to_proposal
from app.engine.loader import load_shared_factors, load_ticker_fixtures, load_timeline
from app.engine.log import DecisionLog
from app.engine.timeline import initial_state_event, run

app = FastAPI(title="Lexo Trading Decision System")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def render_quote(text: str) -> Markup:
    """BUG-20260924-1900-30: source PDFs sometimes carry literal markdown-style
    **bold** in extracted text. The underlying fixture data stays verbatim
    (provenance discipline); this only turns it into real emphasis for display,
    so a plain quote in a blockquote doesn't render literal asterisks."""
    bolded = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", str(escape(text)))
    return Markup(bolded)


templates.env.filters["render_quote"] = render_quote

# ISS-20260924-1732-39: raw action identifiers (move_to_base_row_drift_200_09)
# are what overflowed the dated-triggers table at 390px. Prose is the root-cause
# fix — shorter and more readable at any width, not just scrolled on mobile.
_ACTION_PROSE = {
    "open_starter_position": "Open a starter position",
    "buy_full_weight": "Buy at full weight",
    "move_to_bear_row": "Move to the bear row",
    "move_to_base_row_drift_200_09": "Move to the base row, drift toward $200.09",
    "exit_short": "Exit / go short",
    "sell": "Sell",
    "hedge_existing_exposure": "Hedge existing exposure",
    "stop_exit": "Stop out",
}


def action_prose(action: str) -> str:
    return _ACTION_PROSE.get(action, action)


templates.env.filters["action_prose"] = action_prose


def _inline_markdown(text: str) -> str:
    escaped = str(escape(text))
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    # Single-asterisk italics, after bold so **x** doesn't leave stray *'s behind.
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"`([^`]+?)`", r"<code>\1</code>", escaped)
    return escaped


def render_markdown(text: str) -> Markup:
    """BUG-20260924-1732-36: the write-up (FEAT-14) was rendered as a single
    <pre> block, so its headings/lists/bold/rules showed as literal '#', '-',
    '**', '---' — on the one page carrying the thinking the client said is
    graded as heavily as the code. A small line-oriented parser, not a new
    dependency: headings (#/##/###), bullet and numbered lists (with wrapped
    continuation lines), horizontal rules, bold and inline code, paragraphs.
    Handles exactly the subset WHERE_THIS_GOES_NEXT.md actually uses — this is
    not a general markdown engine."""
    lines = text.split("\n")
    html: list[str] = []
    para_buf: list[str] = []
    list_type: str | None = None

    def flush_para() -> None:
        if para_buf:
            html.append("<p>" + _inline_markdown(" ".join(para_buf)) + "</p>")
            para_buf.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            html.append(f"</{list_type}>")
            list_type = None

    marker_re = re.compile(r"^-\s+(.*)$")
    numbered_re = re.compile(r"^\d+\.\s+(.*)$")
    heading_re = re.compile(r"^(#{1,3})\s+(.*)$")
    is_break = lambda s: s == "" or s == "---" or marker_re.match(s) or numbered_re.match(s) or heading_re.match(s)

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        if stripped == "":
            flush_para()
            close_list()
            i += 1
            continue

        if stripped == "---":
            flush_para()
            close_list()
            html.append("<hr>")
            i += 1
            continue

        heading = heading_re.match(stripped)
        if heading:
            flush_para()
            close_list()
            level = len(heading.group(1))
            html.append(f"<h{level}>{_inline_markdown(heading.group(2))}</h{level}>")
            i += 1
            continue

        bullet = marker_re.match(stripped)
        numbered = numbered_re.match(stripped)
        if bullet or numbered:
            flush_para()
            this_type = "ul" if bullet else "ol"
            if list_type != this_type:
                close_list()
                html.append(f"<{this_type}>")
                list_type = this_type
            item_lines = [(bullet or numbered).group(1)]
            j = i + 1
            while j < len(lines) and not is_break(lines[j].strip()):
                item_lines.append(lines[j].strip())
                j += 1
            html.append("<li>" + _inline_markdown(" ".join(item_lines)) + "</li>")
            i = j
            continue

        close_list()
        para_buf.append(stripped)
        i += 1

    flush_para()
    close_list()
    return Markup("\n".join(html))


templates.env.filters["render_markdown"] = render_markdown

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
    client framework (decided in Turn 4, notepad).

    BUG-20260924-1724-35: an unrecognised scenario used to silently fall back
    to SCENARIOS[0] while the URL still showed the bogus name — a fallback a
    reader can't see, which CLAUDE.md Module 4 forbids. 404 instead."""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"No such scenario: {scenario!r}")
    log = _run_scenario(scenario)
    responses_by_proposal = {e.responds_to: e for e in log.entries if e.kind == "proposal_response"}
    # BUG-20260924-1732-37: proposal_response entries are appended to the log
    # after the run completes (they're recorded later, by a human), so append
    # order isn't chronological order — a response dated 2027-01-28 could
    # render after a 2027-02-04 entry. Sort by (date, id) for display only;
    # the underlying log's append order (and hash) is untouched.
    entries_in_date_order = sorted(log.entries, key=lambda e: (e.date, e.id))
    return templates.TemplateResponse(
        request,
        "timeline.html",
        {
            "scenario": scenario,
            "scenarios": SCENARIOS,
            "entries": entries_in_date_order,
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
    actor, not a reason).

    BUG-20260924-1724-34: proposal_id used to go unvalidated, so any id that
    wasn't a real proposal (unknown, or a valid id that belongs to a
    non-proposal entry) got stored anyway — and every later render of this
    scenario then 500'd forever, calling next() on an empty generator inside
    respond_to_proposal. Validate against a freshly computed log before
    storing anything; reject with 404 rather than accept and break the page.

    BUG-20260924-1724-35: unknown scenario also 404s here now, matching the
    GET route, instead of silently dropping the response."""
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"No such scenario: {scenario!r}")
    log = _run_scenario(scenario)
    valid_proposal_ids = {e.id for e in log.entries if e.kind == "proposal"}
    if proposal_id not in valid_proposal_ids:
        raise HTTPException(status_code=404, detail=f"No such proposal: {proposal_id}")
    _PROPOSAL_RESPONSES[scenario].append((proposal_id, decision))
    return RedirectResponse(url=f"/timeline/{scenario}", status_code=303)
