"""Severity classification engine.

Loads severity-rules.yaml and applies its rules in first-match order against a
facts dict. The mapping from a rule's symbolic "when" condition name to an
evaluator function is the only hardcoded piece here; rule_id, verdict text and
precedence order all come from the published severity-rules.yaml itself, not
from this code. No case IDs, sample IDs, or expected verdicts are embedded.
"""
from __future__ import annotations
import yaml
from dataclasses import dataclass
from typing import Any


REQUIRED_FACT_KEYS = (
    "required_control_design_missing",
    "failed_required_samples",
    "affected_units",
    "prior_major_open_or_repeated",
    "required_evidence_stale_missing_or_hash_failed",
    "population_or_required_procedure_unavailable",
)


def _cond_required_control_design_missing(f: dict) -> bool:
    return bool(f["required_control_design_missing"])


def _cond_failed_gte_2_and_units_gte_2(f: dict) -> bool:
    return f["failed_required_samples"] >= 2 and f["affected_units"] >= 2


def _cond_prior_major_open_or_repeated(f: dict) -> bool:
    return bool(f["prior_major_open_or_repeated"])


def _cond_failed_gte_1(f: dict) -> bool:
    return f["failed_required_samples"] >= 1


def _cond_evidence_stale_missing_hash_failed(f: dict) -> bool:
    return bool(f["required_evidence_stale_missing_or_hash_failed"])


def _cond_population_unavailable(f: dict) -> bool:
    return bool(f["population_or_required_procedure_unavailable"])


def _cond_all_pass_current_valid(f: dict) -> bool:
    return (
        f["failed_required_samples"] == 0
        and not f["required_control_design_missing"]
        and not f["prior_major_open_or_repeated"]
        and not f["required_evidence_stale_missing_or_hash_failed"]
        and not f["population_or_required_procedure_unavailable"]
    )


_CONDITION_EVALUATORS = {
    "required_control_design_missing": _cond_required_control_design_missing,
    "failed_required_samples_gte_2_and_affected_units_gte_2": _cond_failed_gte_2_and_units_gte_2,
    "prior_major_open_or_repeated": _cond_prior_major_open_or_repeated,
    "failed_required_samples_gte_1": _cond_failed_gte_1,
    "required_evidence_stale_missing_or_hash_failed": _cond_evidence_stale_missing_hash_failed,
    "population_or_required_procedure_unavailable": _cond_population_unavailable,
    "all_required_samples_pass_and_evidence_is_current_and_valid": _cond_all_pass_current_valid,
}


class UnknownConditionError(ValueError):
    pass


class MissingFactError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    rule_id: str
    when: str
    verdict: str


@dataclass(frozen=True)
class SeverityRuleset:
    schema_version: str
    verdict_order: tuple
    rules: tuple
    precedence: str
    output_requirements: tuple

    @classmethod
    def load(cls, path: str) -> "SeverityRuleset":
        with open(path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)
        rules = tuple(Rule(r["id"], r["when"], r["verdict"]) for r in raw["rules"])
        for r in rules:
            if r.when not in _CONDITION_EVALUATORS:
                raise UnknownConditionError(
                    f"Rule {r.rule_id} references unknown condition '{r.when}'. "
                    "Refusing to guess; add an evaluator or escalate."
                )
        return cls(
            schema_version=raw["schema_version"],
            verdict_order=tuple(raw["verdict_order"]),
            rules=rules,
            precedence=raw["precedence"],
            output_requirements=tuple(raw["output_requirements"]),
        )

    def classify(self, facts: dict) -> tuple:
        """Return (rule_id, verdict) for the first matching rule.

        Raises MissingFactError if a required fact key is absent -- a test
        must never silently default a missing fact to a passing state.
        """
        missing = [k for k in REQUIRED_FACT_KEYS if k not in facts]
        if missing:
            raise MissingFactError(f"facts missing required keys: {missing}")
        if self.precedence != "first_match":
            raise ValueError(f"unsupported precedence mode: {self.precedence}")
        for rule in self.rules:
            evaluator = _CONDITION_EVALUATORS[rule.when]
            if evaluator(facts):
                return rule.rule_id, rule.verdict
        raise ValueError("no rule matched; facts do not satisfy even the CONFORMS fallback")
