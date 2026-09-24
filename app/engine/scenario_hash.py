"""Print a scenario's canonical decision-log hash. Run as a module so the
determinism test can invoke it in a fresh subprocess with PYTHONHASHSEED varied —
proving the hash is stable across processes, not just reproducible within one."""

import sys

from app.engine.loader import load_ticker_fixtures, load_timeline
from app.engine.timeline import run


def scenario_hash(scenario: str, ticker: str = "NVDA") -> str:
    rules = load_ticker_fixtures(ticker).rules
    events = load_timeline(scenario).events
    return run(rules, events).canonical_hash()


if __name__ == "__main__":
    print(scenario_hash(sys.argv[1]))
