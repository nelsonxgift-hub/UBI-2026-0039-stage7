import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit-engine"))
from engine import run_audit  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
POP_CSV = ROOT / "evidence" / "audit-populations.csv"
SEVERITY_YAML = ROOT / "evidence" / "severity-rules.yaml"
MARKER = "UBI-A7-ADFAFF62AD2E"


def test_clean_state_run_produces_12_tests(tmp_path):
    """Per programme disposition (Somto, UBI programme support): the archived
    audit-test-sheet.csv/brief.md governs, twelve tests, AT-01 through AT-12,
    one per issued control. A single test may draw on multiple procedures,
    samples, or evidence items internally, but remains one issued test."""
    result = run_audit.run(MARKER, str(POP_CSV), str(SEVERITY_YAML), str(tmp_path))
    assert result["n_tests"] == 12
    verdicts = json.loads((tmp_path / "evidence-verdicts.json").read_text())
    assert len(verdicts["tests"]) == 12
    assert verdicts["evidence_marker"] == MARKER


def test_rerun_from_clean_state_is_byte_identical_except_timestamp(tmp_path):
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    run_audit.run(MARKER, str(POP_CSV), str(SEVERITY_YAML), str(out1))
    run_audit.run(MARKER, str(POP_CSV), str(SEVERITY_YAML), str(out2))

    m1 = (out1 / "sample-manifest.csv").read_text()
    m2 = (out2 / "sample-manifest.csv").read_text()
    assert m1 == m2, "sample manifest must be byte-identical across runs with the same marker"

    v1 = json.loads((out1 / "evidence-verdicts.json").read_text())
    v2 = json.loads((out2 / "evidence-verdicts.json").read_text())
    v1["generated_at_utc"] = v2["generated_at_utc"]
    assert v1 == v2


def test_no_verdict_is_conforming_when_a_required_sample_is_missing():
    """A.5.18 merges two evidence requests (Q1 review scope gap, Q2 review
    still in progress at audit-period end). The Q2 piece alone carries
    population_or_required_procedure_unavailable=True; this must survive the
    merge into the single issued A.5.18 test, and the merged verdict must
    never resolve to conforms, regardless of which published rule ends up
    firing first in precedence order (MINOR-EVIDENCE outranks NOT-TESTED, so
    the actual verdict here is minor_nc, not not_tested -- that is correct,
    expected behavior of first-match precedence, not a defect)."""
    from engine.test_definitions import build_tests
    from engine import collector as C
    from engine.test_definitions import AUDIT_PERIOD_END, STALE_AFTER_DAYS

    records = C.load_populations(str(POP_CSV), AUDIT_PERIOD_END, STALE_AFTER_DAYS)
    tests = build_tests(records, MARKER)
    a518 = [t for t in tests if t["control_id"] == "A.5.18"][0]
    assert a518["facts"].population_or_required_procedure_unavailable is True, (
        "the Q2-piece's unavailable-procedure fact must survive the merge into "
        "the single issued A.5.18 test, not be silently dropped"
    )

    from engine.severity import SeverityRuleset
    ruleset = SeverityRuleset.load(str(SEVERITY_YAML))
    rule_id, verdict = ruleset.classify(a518["facts"].as_dict())
    assert verdict != "conforms", (
        f"A.5.18 has an unavailable required procedure but was classified {verdict}"
    )


def test_a_failed_required_sample_never_yields_conforms():
    from engine.test_definitions import build_tests
    from engine import collector as C
    from engine.test_definitions import AUDIT_PERIOD_END, STALE_AFTER_DAYS
    from engine.severity import SeverityRuleset

    records = C.load_populations(str(POP_CSV), AUDIT_PERIOD_END, STALE_AFTER_DAYS)
    tests = build_tests(records, MARKER)
    ruleset = SeverityRuleset.load(str(SEVERITY_YAML))
    for t in tests:
        facts = t["facts"].as_dict()
        if facts["failed_required_samples"] >= 1:
            _, verdict = ruleset.classify(facts)
            assert verdict != "conforms", f"{t['test_id']} has a failed sample but was classified conforms"
