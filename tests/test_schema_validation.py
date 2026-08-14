"""Validates that evidence-verdicts.json and sample-manifest.csv actually
conform to the JSON schemas published in schemas/. Before this test existed,
those schema files were reference documentation only -- nothing in the
pipeline enforced them. This closes that gap: if the engine's output ever
drifts from the published schema, this test fails.
"""
import csv
import json
import sys
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit-engine"))
from engine import run_audit  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def test_evidence_verdicts_matches_its_published_schema(tmp_path):
    run_audit.run(
        "UBI-A7-ADFAFF62AD2E",
        str(ROOT / "evidence" / "audit-populations.csv"),
        str(ROOT / "evidence" / "severity-rules.yaml"),
        str(tmp_path),
    )
    schema = json.loads((SCHEMAS / "evidence-verdicts.schema.json").read_text())
    instance = json.loads((tmp_path / "evidence-verdicts.json").read_text())
    jsonschema.validate(instance=instance, schema=schema)


def test_sample_manifest_rows_match_its_published_schema(tmp_path):
    run_audit.run(
        "UBI-A7-ADFAFF62AD2E",
        str(ROOT / "evidence" / "audit-populations.csv"),
        str(ROOT / "evidence" / "severity-rules.yaml"),
        str(tmp_path),
    )
    schema = json.loads((SCHEMAS / "sample-manifest.schema.json").read_text())
    with open(tmp_path / "sample-manifest.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows, "sample-manifest.csv produced no rows to validate"
    for row in rows:
        # CSV values are strings; coerce the two integer fields the schema
        # declares before validating, since CSV has no native int type.
        coerced = dict(row)
        coerced["eligible_count"] = int(row["eligible_count"])
        coerced["sample_size"] = int(row["sample_size"])
        coerced["included"] = row["included"] in ("True", "true", "1")
        jsonschema.validate(instance=coerced, schema=schema)


def test_committed_evidence_verdicts_json_also_matches_schema():
    """The frozen, already-committed evidence-verdicts.json at the submission
    root must itself satisfy the schema, not just a freshly regenerated copy."""
    schema = json.loads((SCHEMAS / "evidence-verdicts.schema.json").read_text())
    instance = json.loads((ROOT / "evidence-verdicts.json").read_text())
    jsonschema.validate(instance=instance, schema=schema)
