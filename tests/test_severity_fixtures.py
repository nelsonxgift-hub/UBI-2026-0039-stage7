"""Validates the severity engine against every one of the 24 published
fixtures in evidence/brief/public-fixtures.json. This is the published
acceptance suite referenced by the technical assessment contract."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit-engine"))
from engine.severity import SeverityRuleset  # noqa: E402

FIXTURES_PATH = Path(__file__).resolve().parents[1] / "evidence" / "public-fixtures.json"
SEVERITY_PATH = Path(__file__).resolve().parents[1] / "evidence" / "severity-rules.yaml"


def _load_fixtures():
    with open(FIXTURES_PATH, encoding="utf-8") as fh:
        return json.load(fh)["fixtures"]


def _facts_from_fixture(fx):
    f = fx["facts"]
    return {
        "required_control_design_missing": f["required_control_design_missing"],
        "failed_required_samples": f["failed_required_samples"],
        "affected_units": f["affected_units"],
        "prior_major_open_or_repeated": f["prior_major_open_or_repeated"],
        "required_evidence_stale_missing_or_hash_failed": f["required_evidence_stale_missing_or_hash_failed"],
        "population_or_required_procedure_unavailable": f["population_or_required_procedure_unavailable"],
    }


def test_all_24_public_fixtures_classify_correctly():
    ruleset = SeverityRuleset.load(str(SEVERITY_PATH))
    fixtures = _load_fixtures()
    assert len(fixtures) == 24
    failures = []
    for fx in fixtures:
        rule_id, verdict = ruleset.classify(_facts_from_fixture(fx))
        expected = fx["expected"]
        if rule_id != expected["rule_id"] or verdict != expected["verdict"]:
            failures.append((fx["case_id"], (rule_id, verdict), (expected["rule_id"], expected["verdict"])))
    assert not failures, f"Fixture mismatches: {failures}"


def test_fixture_count_matches_published_total():
    assert len(_load_fixtures()) == 24
