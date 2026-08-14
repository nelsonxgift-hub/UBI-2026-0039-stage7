"""Not one of the 24 published fixtures. Same schema, different case IDs,
ordering, and boundary values, written by hand to sanity-check that the
severity engine generalizes rather than pattern-matching the published set.
This is a stand-in for the staff hidden fixture; it does not claim to BE
the staff hidden fixture (that pack is not available to the candidate)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit-engine"))
from engine.severity import SeverityRuleset  # noqa: E402

SEVERITY_PATH = Path(__file__).resolve().parents[1] / "evidence" / "severity-rules.yaml"

_BASE = dict(
    required_control_design_missing=False,
    failed_required_samples=0,
    affected_units=0,
    prior_major_open_or_repeated=False,
    required_evidence_stale_missing_or_hash_failed=False,
    population_or_required_procedure_unavailable=False,
)


def _facts(**overrides):
    f = dict(_BASE)
    f.update(overrides)
    return f


TRANSFER_CASES = [
    # boundary: exactly at the gte thresholds, not one above them
    ("boundary-systemic-exact-2-2", _facts(failed_required_samples=2, affected_units=2), "MAJOR-SYSTEMIC", "major_nc"),
    # boundary: just under the systemic threshold on one axis -> falls through to minor
    ("boundary-systemic-2-failed-1-unit", _facts(failed_required_samples=2, affected_units=1), "MINOR-OPERATING", "minor_nc"),
    ("boundary-systemic-1-failed-2-units", _facts(failed_required_samples=1, affected_units=2), "MINOR-OPERATING", "minor_nc"),
    # design-missing outranks everything else, even a simultaneous systemic pattern
    ("design-missing-outranks-systemic", _facts(required_control_design_missing=True, failed_required_samples=5, affected_units=5), "MAJOR-DESIGN", "major_nc"),
    # recurrence outranks minor-operating even with only 1 failed sample
    ("recurrence-with-single-failure", _facts(prior_major_open_or_repeated=True, failed_required_samples=1, affected_units=1), "MAJOR-RECURRENCE", "major_nc"),
    # stale evidence alone, no failed samples
    ("stale-only-zero-failures", _facts(required_evidence_stale_missing_or_hash_failed=True), "MINOR-EVIDENCE", "minor_nc"),
    # unavailable procedure outranks a conforms-looking clean facts set
    ("unavailable-with-otherwise-clean-facts", _facts(population_or_required_procedure_unavailable=True), "NOT-TESTED", "not_tested"),
    # true clean pass
    ("clean-pass", _facts(), "CONFORMS", "conforms"),
    # large failed count with only 1 affected unit stays minor (repeated failures, same unit)
    ("many-failures-one-unit", _facts(failed_required_samples=9, affected_units=1), "MINOR-OPERATING", "minor_nc"),
]


def test_transfer_style_cases_not_in_published_fixture_set():
    ruleset = SeverityRuleset.load(str(SEVERITY_PATH))
    failures = []
    for case_id, facts, expected_rule, expected_verdict in TRANSFER_CASES:
        rule_id, verdict = ruleset.classify(facts)
        if rule_id != expected_rule or verdict != expected_verdict:
            failures.append((case_id, (rule_id, verdict), (expected_rule, expected_verdict)))
    assert not failures, f"Transfer-style mismatches: {failures}"
