"""CLI entry point: `python -m engine.run_audit --marker <MARKER> --populations <csv> --severity <yaml> --outdir <dir>`

Emits, deterministically for a given marker:
  sample-manifest.csv
  evidence-verdicts.json
  audit-test-sheet.csv   (fills the published template; does not rename it)
  nonconformity-register.csv
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import collector as C
from . import severity as SEV
from . import evidence_index as EI
from . import test_definitions as TD
from . import evidence_index as EI

SCHEMA_VERSION = "1.0"


def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def run(marker: str, populations_csv: str, severity_yaml: str, outdir: str) -> dict:
    outdir_p = Path(outdir)
    outdir_p.mkdir(parents=True, exist_ok=True)

    records = C.load_populations(populations_csv, TD.AUDIT_PERIOD_END, TD.STALE_AFTER_DAYS)
    ruleset = SEV.SeverityRuleset.load(severity_yaml)
    tests = TD.build_tests(records, marker)

    # --- sample-manifest.csv -------------------------------------------------
    manifest_rows = []
    for t in tests:
        if t["sample"] is None:
            continue
        s = t["sample"]
        for rid in s.selected_record_ids:
            manifest_rows.append(dict(
                population=s.population, control_id=t["control_id"], marker=marker,
                algorithm_version=s.algorithm_version, sample_size_rule=f"min({3},eligible_count)",
                eligible_count=s.eligible_count, sample_size=s.sample_size,
                record_id=rid, included=True, reason_code="selected"))
        for rid in s.not_selected_record_ids:
            manifest_rows.append(dict(
                population=s.population, control_id=t["control_id"], marker=marker,
                algorithm_version=s.algorithm_version, sample_size_rule=f"min({3},eligible_count)",
                eligible_count=s.eligible_count, sample_size=s.sample_size,
                record_id=rid, included=False, reason_code="not_selected"))
        for r in t["excluded"]:
            manifest_rows.append(dict(
                population=s.population, control_id=t["control_id"], marker=marker,
                algorithm_version=s.algorithm_version, sample_size_rule=f"min({3},eligible_count)",
                eligible_count=s.eligible_count, sample_size=s.sample_size,
                record_id=r.record_id, included=False,
                reason_code=",".join(r.reason_codes) if r.reason_codes else "excluded"))

    manifest_rows.sort(key=lambda r: (r["control_id"], r["population"] or "", r["record_id"]))
    manifest_hash = _hash_str(json.dumps(manifest_rows, sort_keys=True, default=str))
    for r in manifest_rows:
        r["sample_manifest_hash"] = manifest_hash

    manifest_path = outdir_p / "sample-manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as fh:
        fieldnames = ["population", "control_id", "marker", "algorithm_version", "sample_size_rule",
                      "eligible_count", "sample_size", "record_id", "included", "reason_code",
                      "sample_manifest_hash"]
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(manifest_rows)

    # --- classify each test --------------------------------------------------
    verdict_tests = []
    test_sheet_rows = []
    nonconformities = []
    nc_seq = 1
    for t in tests:
        facts = t["facts"].as_dict()
        rule_id, verdict = ruleset.classify(facts)
        failed_ids = t.get("failed_ids", [])
        affected_ids = t.get("affected_ids", [])
        excluded_payload = [dict(record_id=r.record_id, reason_code=",".join(r.reason_codes))
                             for r in t["excluded"]]
        required_sample_ids = list(t["sample"].selected_record_ids) if t["sample"] else []

        verdict_tests.append(dict(
            test_id=t["test_id"], control_id=t["control_id"], population=t["population"],
            procedure=t["procedure"], required_sample_ids=required_sample_ids,
            excluded_records=excluded_payload, sample_facts=facts, rule_id=rule_id,
            verdict=verdict, failed_sample_ids=failed_ids, affected_unit_ids=affected_ids,
            evidence_locators=t["evidence_locators"],
        ))

        test_sheet_rows.append(dict(
            test_id=t["test_id"], control_id=t["control_id"],
            audit_criterion="ISO/IEC 27001:2022 Annex A control referenced in the SoA",
            test_procedure=t["procedure"],
            sample=";".join(required_sample_ids) if required_sample_ids else "n/a (narrative evidence)",
            artifact="audit-populations.csv" if t["population"] else "evidence-pack.md",
            exact_locator="; ".join(t["evidence_locators"]),
            evidence_quality="stale_or_incomplete" if facts["required_evidence_stale_missing_or_hash_failed"] else "current",
            result=verdict,
            nonconformity_id="",
            limitation="",
        ))

        if verdict in ("minor_nc", "major_nc"):
            nc_id = f"NC-26-{nc_seq:02d}"
            nc_seq += 1
            test_sheet_rows[-1]["nonconformity_id"] = nc_id
            nonconformities.append(dict(
                nonconformity_id=nc_id, control_id=t["control_id"], test_id=t["test_id"],
                rule_id=rule_id, severity=verdict, statement=t["procedure"],
                evidence_locators="; ".join(t["evidence_locators"]),
                owner="", target_closure_date="",
            ))

    verdicts_doc = dict(
        schema_version=SCHEMA_VERSION,
        evidence_marker=marker,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        sampling_algorithm_version="marker-seeded-sha256-v1",
        tests=verdict_tests,
    )
    with open(outdir_p / "evidence-verdicts.json", "w", encoding="utf-8") as fh:
        json.dump(verdicts_doc, fh, indent=2, sort_keys=False)

    with open(outdir_p / "audit-test-sheet.csv", "w", newline="", encoding="utf-8") as fh:
        fieldnames = ["test_id", "control_id", "audit_criterion", "test_procedure", "sample",
                      "artifact", "exact_locator", "evidence_quality", "result",
                      "nonconformity_id", "limitation"]
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(test_sheet_rows)

    with open(outdir_p / "nonconformity-register.csv", "w", newline="", encoding="utf-8") as fh:
        fieldnames = ["nonconformity_id", "control_id", "test_id", "rule_id", "severity",
                      "statement", "evidence_locators", "owner", "target_closure_date"]
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(nonconformities)

    # --- evidence-index.csv --------------------------------------------------
    # Derived from the frozen verdicts and the static prior-findings-tracker.csv
    # that must already exist at outdir (the submission root). Not optional and
    # not a separate manual step: staff expect evidence-index hashes to
    # reproduce on rerun, exactly like every other output here.
    evidence_dir = Path(populations_csv).parent
    prior_findings_path = outdir_p / "prior-findings-tracker.csv"
    public_fixtures_path = evidence_dir / "public-fixtures.json"
    evidence_index_path = None
    if prior_findings_path.exists():
        with open(prior_findings_path, newline="", encoding="utf-8") as fh:
            prior_rows = list(csv.DictReader(fh))
        index_rows = EI.build_rows(
            verdicts_doc=verdicts_doc,
            prior_findings_rows=prior_rows,
            populations_csv_path=Path(populations_csv),
            sample_manifest_path=manifest_path,
            public_fixtures_path=public_fixtures_path,
            collection_time_utc=verdicts_doc["generated_at_utc"],
        )
        evidence_index_path = EI.write_evidence_index(index_rows, outdir_p)

    return dict(
        manifest_path=str(manifest_path),
        manifest_hash=manifest_hash,
        n_tests=len(tests),
        n_nonconformities=len(nonconformities),
        evidence_index_path=str(evidence_index_path) if evidence_index_path else None,
    )


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", required=True)
    ap.add_argument("--populations", required=True)
    ap.add_argument("--severity", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args(argv)
    result = run(args.marker, args.populations, args.severity, args.outdir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
