from pathlib import Path

import yaml
from pydantic import ValidationError

from app.engine.models import FixtureBundle, Ticker

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


class FixtureLoadError(Exception):
    """Fixtures are missing, malformed, or lack required provenance. Fatal — never caught to fall back."""


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise FixtureLoadError(f"missing fixture file: {path}")
    with path.open() as f:
        data = yaml.safe_load(f)
    if data is None:
        raise FixtureLoadError(f"empty fixture file: {path}")
    return data


def load_ticker_fixtures(ticker: Ticker, fixtures_dir: Path = FIXTURES_DIR) -> FixtureBundle:
    """Load and validate every fixture file for one ticker. Raises FixtureLoadError on any
    missing file, malformed YAML, or claim lacking required provenance — by design, so the
    app never boots on an unsourced rule or factor (CLAUDE.md Module 4)."""
    base = fixtures_dir / ticker.lower()

    research = _read_yaml(base / "research.yaml")
    scenarios = _read_yaml(base / "scenarios.yaml")
    rules = _read_yaml(base / "rules.yaml")
    factors = _read_yaml(base / "factors.yaml")
    catalysts = _read_yaml(base / "catalysts.yaml")

    try:
        return FixtureBundle(
            ticker=ticker,
            research=research,
            scenarios=scenarios.get("scenarios", []),
            rules=rules.get("rules", []),
            overrides=rules.get("overrides", []),
            kill_switches=catalysts.get("kill_switches", []),
            factors=factors.get("factors", []),
        )
    except ValidationError as e:
        raise FixtureLoadError(f"invalid fixtures for {ticker} in {base}: {e}") from e


def load_all_fixtures(tickers: list[Ticker], fixtures_dir: Path = FIXTURES_DIR) -> dict[Ticker, FixtureBundle]:
    return {ticker: load_ticker_fixtures(ticker, fixtures_dir) for ticker in tickers}
