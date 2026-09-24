import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.engine.loader import load_ticker_fixtures, load_timeline
from app.engine.scenario_hash import scenario_hash
from app.engine.timeline import run

REPO_ROOT = Path(__file__).parent.parent

# Recorded so an accidental change to decision logic fails loudly here rather
# than silently producing a different-but-still-internally-consistent answer
# (spec §7). Regenerate deliberately with:
#   uv run python -m app.engine.scenario_hash <scenario>
EXPECTED_HASHES = {
    "guide_holds": "8ae1e19d1c2cb8050d3ee6778c3a02d84371d30a24d8312c7f5cc87e988b8fc5",
    "capex_turns": "95cf62419fa7cb72704daa831ebde1072634d804a70ca427ce6aff0d5575b8b7",
}


@pytest.mark.parametrize("scenario", ["guide_holds", "capex_turns"])
def test_expected_hash_recorded(scenario):
    assert scenario_hash(scenario) == EXPECTED_HASHES[scenario]


@pytest.mark.parametrize("scenario", ["guide_holds", "capex_turns"])
def test_same_process_run_twice_matches(scenario):
    rules = load_ticker_fixtures("NVDA").rules
    events = load_timeline(scenario).events
    assert run(rules, events).canonical_hash() == run(rules, events).canonical_hash()


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
