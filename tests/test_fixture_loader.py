import yaml
import pytest
from pydantic import ValidationError

from app.engine.loader import FixtureLoadError, load_ticker_fixtures
from app.engine.models import Rule, Source

VALID_RESEARCH = {
    "ticker": "NVDA",
    "as_of": "2026-09-08",
    "reference_price": 230.36,
    "stance": "Hold",
    "conviction": "Low",
    "position": "none",
    "horizon": "6-12 months tactical",
    "spring_state": "Neutral",
    "source": {"doc": "NVDA-memo", "page": 46, "quote": "Hold, low conviction, no position initiated."},
    "provenance_status": "derived",
}

VALID_SCENARIOS = {
    "scenarios": [
        {
            "horizon": "intrinsic_3_5yr",
            "weighted_price": 136.78,
            "weighted_return_pct": -40.6,
            "legs": [
                {
                    "label": "base",
                    "probability": 0.5,
                    "price": 139.24,
                    "return_pct": -39.6,
                    "source": {"doc": "NVDA-memo", "page": 44, "quote": "Base 50% $139.24"},
                    "provenance_status": "derived",
                }
            ],
        }
    ]
}

VALID_RULES = {
    "rules": [
        {
            "id": "stop-195",
            "name": "$195 stop, two consecutive weekly closes",
            "ticker": "NVDA",
            "applies_when": "position != none",
            "trigger": {
                "metric": "price_close",
                "comparator": "lte",
                "threshold": 195.0,
                "consecutive_periods": 2,
            },
            "action": "stop_exit",
            "source": {"doc": "NVDA-memo", "page": 46, "quote": "$195.00 on two consecutive weekly closes"},
            "provenance_status": "derived",
        }
    ],
    "overrides": [],
}

VALID_FACTORS = {
    "factors": [
        {
            "id": "guidance-bet",
            "ticker": "NVDA",
            "name": "Guidance Bet",
            "ring": "internal",
            "force": "wave",
            "impact": 0.8,
            "weight": 21,
            "direction": "negative",
            "source": {"doc": "NVDA-factor", "page": 12, "quote": "Guidance Bet, weight 21"},
            "provenance_status": "derived",
        }
    ]
}

VALID_CATALYSTS = {"kill_switches": []}


def _write_ticker_fixtures(tmp_path, ticker="nvda", **overrides):
    base = tmp_path / ticker
    base.mkdir()
    files = {
        "research.yaml": overrides.get("research", VALID_RESEARCH),
        "scenarios.yaml": overrides.get("scenarios", VALID_SCENARIOS),
        "rules.yaml": overrides.get("rules", VALID_RULES),
        "factors.yaml": overrides.get("factors", VALID_FACTORS),
        "catalysts.yaml": overrides.get("catalysts", VALID_CATALYSTS),
    }
    for name, content in files.items():
        (base / name).write_text(yaml.safe_dump(content))
    return tmp_path


def test_valid_fixtures_load(tmp_path):
    fixtures_dir = _write_ticker_fixtures(tmp_path)
    bundle = load_ticker_fixtures("NVDA", fixtures_dir)
    assert bundle.research.stance == "Hold"
    assert bundle.rules[0].id == "stop-195"
    assert bundle.factors[0].weight == 21


def test_missing_fixture_file_fails_fast(tmp_path):
    base = tmp_path / "nvda"
    base.mkdir()
    with pytest.raises(FixtureLoadError, match="missing fixture file"):
        load_ticker_fixtures("NVDA", tmp_path)


def test_rule_without_source_fails_fast(tmp_path):
    bad_rules = {
        "rules": [{**VALID_RULES["rules"][0], "source": None, "provenance_status": "derived"}],
        "overrides": [],
    }
    fixtures_dir = _write_ticker_fixtures(tmp_path, rules=bad_rules)
    with pytest.raises(FixtureLoadError, match="invalid fixtures"):
        load_ticker_fixtures("NVDA", fixtures_dir)


def test_factor_partial_without_gap_note_fails_fast(tmp_path):
    bad_factors = {
        "factors": [{**VALID_FACTORS["factors"][0], "provenance_status": "partial", "gap_note": None}]
    }
    fixtures_dir = _write_ticker_fixtures(tmp_path, factors=bad_factors)
    with pytest.raises(FixtureLoadError, match="invalid fixtures"):
        load_ticker_fixtures("NVDA", fixtures_dir)


def test_added_rule_with_fabricated_source_fails_fast(tmp_path):
    bad_rules = {
        "rules": [
            {
                **VALID_RULES["rules"][0],
                "provenance_status": "added",
                "rationale": "build shortcut",
                "source": {"doc": "NVDA-memo", "page": 1, "quote": "not really"},
            }
        ],
        "overrides": [],
    }
    fixtures_dir = _write_ticker_fixtures(tmp_path, rules=bad_rules)
    with pytest.raises(FixtureLoadError, match="invalid fixtures"):
        load_ticker_fixtures("NVDA", fixtures_dir)


def test_added_rule_without_rationale_fails_fast(tmp_path):
    bad_rules = {
        "rules": [{**VALID_RULES["rules"][0], "provenance_status": "added", "source": None}],
        "overrides": [],
    }
    fixtures_dir = _write_ticker_fixtures(tmp_path, rules=bad_rules)
    with pytest.raises(FixtureLoadError, match="invalid fixtures"):
        load_ticker_fixtures("NVDA", fixtures_dir)


def test_source_model_rejects_empty_quote():
    with pytest.raises(ValidationError):
        Source(doc="NVDA-memo", page=1, quote="")


def test_added_provenance_rejects_a_source_directly():
    with pytest.raises(ValidationError):
        Rule(
            id="x",
            name="x",
            trigger={"metric": "price_close", "comparator": "lte", "threshold": 1},
            action="hold",
            source={"doc": "NVDA-memo", "page": 1, "quote": "q"},
            provenance_status="added",
            rationale="build shortcut",
        )
