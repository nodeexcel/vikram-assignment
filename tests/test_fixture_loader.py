import yaml
import pytest
from pydantic import ValidationError

from app.engine.loader import FixtureLoadError, load_shared_factors, load_ticker_fixtures
from app.engine.models import Factor, Rule, Source, Trigger

VALID_RESEARCH = {
    "ticker": "NVDA",
    "as_of": "2026-09-08",
    "reference_price": 230.36,
    "verdict": {
        "text": "Diamond in Air | Ocean | Luminous - N-of-1, 83/100",
        "source": {"doc": "NVDA-memo", "page": 3, "quote": "Lexo Verdict: Diamond in Air | Ocean | Luminous."},
        "provenance_status": "derived",
    },
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
            "requires_existing_position": True,
            "trigger": {
                "metric": "price_close",
                "comparator": "lte",
                "threshold": 195.0,
                "consecutive_periods": 2,
                "period_unit": "weekly",
            },
            "action": "stop_exit",
            "source": {"doc": "NVDA-memo", "page": 46, "quote": "$195.00 on two consecutive weekly closes"},
            "provenance_status": "derived",
        }
    ],
    "overrides": [],
}

VALID_CATALYSTS = {"kill_switches": []}

VALID_EXPOSURE_SOURCE = {"doc": "NVDA-factor", "page": 12, "quote": "some verified quote"}


def _write_ticker_fixtures(tmp_path, ticker="nvda", **overrides):
    base = tmp_path / ticker
    base.mkdir()
    files = {
        "research.yaml": overrides.get("research", VALID_RESEARCH),
        "scenarios.yaml": overrides.get("scenarios", VALID_SCENARIOS),
        "rules.yaml": overrides.get("rules", VALID_RULES),
        "catalysts.yaml": overrides.get("catalysts", VALID_CATALYSTS),
    }
    for name, content in files.items():
        (base / name).write_text(yaml.safe_dump(content))
    return tmp_path


def _write_factors(tmp_path, factors):
    (tmp_path / "factors.yaml").write_text(yaml.safe_dump({"factors": factors}))


def _sector_factor(**overrides):
    factor = {
        "id": "hyperscaler_capex_financing_shift",
        "ring": "market",
        "force": "wave",
        "label": "Hyperscaler capex turning credit-funded",
        "exposures": {
            "NVDA": {
                "local_id": 22,
                "local_name": "Hyperscaler Capex Financing Shift",
                "direction": "negative",
                "impact": 0.90,
                "weight": 13,
                "source": VALID_EXPOSURE_SOURCE,
                "provenance_status": "derived",
            },
            "AMZN": {
                "local_id": 24,
                "local_name": "Open Credit Funding AI Cloud Customers",
                "direction": "positive",
                "impact": 0.70,
                "source": VALID_EXPOSURE_SOURCE,
                "provenance_status": "derived",
            },
        },
    }
    factor.update(overrides)
    return factor


def test_valid_ticker_fixtures_load(tmp_path):
    fixtures_dir = _write_ticker_fixtures(tmp_path)
    bundle = load_ticker_fixtures("NVDA", fixtures_dir)
    assert bundle.research.stance == "Hold"
    assert bundle.rules[0].id == "stop-195"


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


def test_shared_sector_factor_with_two_exposures_loads(tmp_path):
    _write_factors(tmp_path, [_sector_factor()])
    factors = load_shared_factors(tmp_path)
    assert len(factors) == 1
    factor = factors[0]
    assert factor.ring == "market"
    assert set(factor.exposures) == {"NVDA", "AMZN"}
    assert factor.exposures["NVDA"].direction == "negative"
    assert factor.exposures["AMZN"].direction == "positive"


def test_sector_factor_with_single_exposure_is_legal(tmp_path):
    factor = _sector_factor(ring="sector")
    del factor["exposures"]["AMZN"]
    _write_factors(tmp_path, [factor])
    factors = load_shared_factors(tmp_path)
    assert len(factors[0].exposures) == 1


def test_internal_factor_with_two_exposures_is_a_startup_error(tmp_path):
    factor = _sector_factor(ring="internal")
    _write_factors(tmp_path, [factor])
    with pytest.raises(FixtureLoadError, match="internal-ring"):
        load_shared_factors(tmp_path)


def test_factor_exposure_missing_source_fails_fast(tmp_path):
    factor = _sector_factor()
    factor["exposures"]["NVDA"]["source"] = None
    _write_factors(tmp_path, [factor])
    with pytest.raises(FixtureLoadError, match="invalid factors"):
        load_shared_factors(tmp_path)


def test_factor_model_rejects_empty_exposures_directly():
    with pytest.raises(ValidationError):
        Factor(id="x", ring="market", force="wave", label="x", exposures={})


def test_unknown_ring_factor_with_two_exposures_is_a_startup_error(tmp_path):
    factor = _sector_factor(ring="unknown")
    _write_factors(tmp_path, [factor])
    with pytest.raises(FixtureLoadError, match="unknown-ring"):
        load_shared_factors(tmp_path)


def test_override_with_unresolved_rule_id_fails_fast(tmp_path):
    bad_rules = {
        "rules": VALID_RULES["rules"],
        "overrides": [
            {
                "id": "override-1",
                "rule_id": "no-such-rule",
                "would_have_done": "x",
                "actual": "y",
                "reason": "z",
                "actor": "memo",
                "source": {"doc": "NVDA-memo", "page": 1, "quote": "q"},
                "provenance_status": "derived",
            }
        ],
    }
    fixtures_dir = _write_ticker_fixtures(tmp_path, rules=bad_rules)
    with pytest.raises(FixtureLoadError, match="targets rule_id"):
        load_ticker_fixtures("NVDA", fixtures_dir)


def test_override_with_resolved_rule_id_loads(tmp_path):
    bad_rules = {
        "rules": VALID_RULES["rules"],
        "overrides": [
            {
                "id": "override-1",
                "rule_id": "stop-195",
                "would_have_done": "x",
                "actual": "y",
                "reason": "z",
                "actor": "memo",
                "source": {"doc": "NVDA-memo", "page": 1, "quote": "q"},
                "provenance_status": "derived",
            }
        ],
    }
    fixtures_dir = _write_ticker_fixtures(tmp_path, rules=bad_rules)
    bundle = load_ticker_fixtures("NVDA", fixtures_dir)
    assert bundle.overrides[0].rule_id == "stop-195"


def test_consecutive_periods_without_period_unit_is_rejected():
    with pytest.raises(ValidationError, match="period_unit"):
        Trigger(metric="price_close", comparator="lte", threshold=195.0, consecutive_periods=2)


def test_upper_threshold_expresses_a_closed_range():
    trigger = Trigger(metric="fy2028_commentary_pct", comparator="gte", threshold=45, upper_threshold=70)
    assert trigger.threshold == 45
    assert trigger.upper_threshold == 70


def test_ordering_comparator_against_string_threshold_is_rejected():
    with pytest.raises(ValidationError, match="orderable"):
        Trigger(metric="spring_state", comparator="gte", threshold="Neutral")


def test_categorical_eq_comparator_accepts_string_threshold():
    trigger = Trigger(metric="spring_state", comparator="eq", threshold="Neutral")
    assert trigger.threshold == "Neutral"
