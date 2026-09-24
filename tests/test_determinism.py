import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.engine.loader import load_shared_factors, load_ticker_fixtures, load_timeline
from app.engine.scenario_hash import scenario_hash
from app.engine.timeline import initial_state_event, run

REPO_ROOT = Path(__file__).parent.parent

# Recorded so an accidental change to decision logic fails loudly here rather
# than silently producing a different-but-still-internally-consistent answer
# (spec §7). Regenerate deliberately with:
#   uv run python -m app.engine.scenario_hash <scenario>
EXPECTED_HASHES = {
    "guide_holds": "a07a2384eb359f70663ccbb1394ab96449de40b0a2b8808da09b950bdadc40c4",
    "capex_turns": "ee1cb6be2b7c9e04472660f65280abebf88d9b3eb5d979e9253c25ba948c20a1",
}


@pytest.mark.parametrize("scenario", ["guide_holds", "capex_turns"])
def test_expected_hash_recorded(scenario):
    assert scenario_hash(scenario) == EXPECTED_HASHES[scenario]


@pytest.mark.parametrize("scenario", ["guide_holds", "capex_turns"])
def test_same_process_run_twice_matches(scenario):
    bundle = load_ticker_fixtures("NVDA")
    factors = load_shared_factors()
    events = [initial_state_event(bundle.research), *load_timeline(scenario).events]
    hash_a = run(bundle.rules, events, bundle.overrides, factors).canonical_hash()
    hash_b = run(bundle.rules, events, bundle.overrides, factors).canonical_hash()
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
