"""Print a scenario's canonical decision-log hash. Run as a module so the
determinism test can invoke it in a fresh subprocess with PYTHONHASHSEED varied —
proving the hash is stable across processes, not just reproducible within one."""

import sys

from app.engine.loader import load_shared_factors, load_ticker_fixtures, load_timeline
from app.engine.timeline import initial_state_event, run


def scenario_hash(scenario: str, ticker: str = "NVDA") -> str:
    bundle = load_ticker_fixtures(ticker)
    factors = load_shared_factors()
    events = [initial_state_event(bundle.research), *load_timeline(scenario).events]
    return run(bundle.rules, events, bundle.overrides, factors).canonical_hash()


if __name__ == "__main__":
    print(scenario_hash(sys.argv[1]))
