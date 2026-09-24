from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.engine.loader import load_ticker_fixtures, load_timeline
from app.engine.timeline import run

app = FastAPI(title="Lexo Trading Decision System")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

SCENARIOS = ["guide_holds", "capex_turns"]


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/determinism")
def determinism(request: Request):
    """Visible determinism check (spec §7): re-runs each scenario twice and shows
    both canonical hashes side by side with a match indicator. "Show us that it
    holds" — shown, not just asserted in a test file nobody but us reads."""
    rules = load_ticker_fixtures("NVDA").rules
    checks = []
    for scenario in SCENARIOS:
        events = load_timeline(scenario).events
        hash_a = run(rules, events).canonical_hash()
        hash_b = run(rules, events).canonical_hash()
        checks.append({"scenario": scenario, "hash_a": hash_a, "hash_b": hash_b, "match": hash_a == hash_b})
    return templates.TemplateResponse(request, "determinism.html", {"checks": checks})
