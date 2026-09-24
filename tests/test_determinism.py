import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.engine.loader import load_ticker_fixtures, load_timeline
from app.engine.scenario_hash import scenario_hash
from app.engine.timeline import initial_state_event, run

REPO_ROOT = Path(__file__).parent.parent

# Recorded so an accidental change to decision logic fails loudly here rather
# than silently producing a different-but-still-internally-consistent answer
# (spec §7). Regenerate deliberately with:
#   uv run python -m app.engine.scenario_hash <scenario>
EXPECTED_HASHES = {
    "guide_holds": "90d17f97f273b38bde1f7354b51136e668372a5a2032df5ac1763394f9eb645a",
    "capex_turns": "8a4b16f7b425a02aa0cdf2c81007373479847ad3517a44323f685071af38a130",
}


@pytest.mark.parametrize("scenario", ["guide_holds", "capex_turns"])
def test_expected_hash_recorded(scenario):
    assert scenario_hash(scenario) == EXPECTED_HASHES[scenario]


@pytest.mark.parametrize("scenario", ["guide_holds", "capex_turns"])
def test_same_process_run_twice_matches(scenario):
    bundle = load_ticker_fixtures("NVDA")
    events = [initial_state_event(bundle.research), *load_timeline(scenario).events]
    hash_a = run(bundle.rules, events, bundle.overrides).canonical_hash()
    hash_b = run(bundle.rules, events, bundle.overrides).canonical_hash()
    assert hash_a == hash_b


@pytest.mark.parametrize("scenario", ["guide_holds", "capex_turns"])
def test_subprocess_with_varied_hash_seed_matches(scenario):
    """spec §7: run once in-process and once in a subprocess with PYTHONHASHSEED
    varied; the hashes must be equal. This is the actual proof against hidden
    dict/set-iteration-order dependence — code review can miss it, a differently-
    seeded process run cannot."""
    in_process = scenario_hash(scenario)

    result = subprocess.run(
        [sys.executable, "-m", "app.engine.scenario_hash", scenario],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONHASHSEED": "918273645"},
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess_hash = result.stdout.strip()

    assert subprocess_hash == in_process
