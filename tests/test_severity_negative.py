import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit-engine"))
from engine.severity import SeverityRuleset, MissingFactError, UnknownConditionError  # noqa: E402

SEVERITY_PATH = Path(__file__).resolve().parents[1] / "evidence" / "severity-rules.yaml"


def test_missing_fact_key_raises_rather_than_defaulting_to_pass():
    ruleset = SeverityRuleset.load(str(SEVERITY_PATH))
    incomplete_facts = {
        "required_control_design_missing": False,
        "failed_required_samples": 0,
        # affected_units intentionally omitted
        "prior_major_open_or_repeated": False,
        "required_evidence_stale_missing_or_hash_failed": False,
        "population_or_required_procedure_unavailable": False,
    }
    with pytest.raises(MissingFactError):
        ruleset.classify(incomplete_facts)


def test_unknown_condition_in_severity_yaml_is_rejected_at_load(tmp_path):
    bad_yaml = tmp_path / "bad-severity.yaml"
    bad_yaml.write_text(
        "schema_version: \"1.0\"\n"
        "verdict_order: [not_tested, conforms, minor_nc, major_nc]\n"
        "rules:\n"
        "  - id: MADE-UP\n"
        "    when: something_not_defined_anywhere\n"
        "    verdict: major_nc\n"
        "precedence: first_match\n"
        "output_requirements: [rule_id]\n"
    )
    with pytest.raises(UnknownConditionError):
        SeverityRuleset.load(str(bad_yaml))


def test_unsupported_precedence_mode_is_rejected():
    ruleset = SeverityRuleset.load(str(SEVERITY_PATH))
    forced = ruleset.__class__(
        schema_version=ruleset.schema_version,
        verdict_order=ruleset.verdict_order,
        rules=ruleset.rules,
        precedence="last_match",
        output_requirements=ruleset.output_requirements,
    )
    all_pass_facts = {
        "required_control_design_missing": False,
        "failed_required_samples": 0,
        "affected_units": 0,
        "prior_major_open_or_repeated": False,
        "required_evidence_stale_missing_or_hash_failed": False,
        "population_or_required_procedure_unavailable": False,
    }
    with pytest.raises(ValueError):
        forced.classify(all_pass_facts)
