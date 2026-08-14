"""Proves evidence-index.csv is now a real, reproducible build artifact, not
a hand-typed file. The brief states staff will rerun the collector with the
same marker and expect identical evidence-index hashes; this test is the
direct check against that specific claim.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit-engine"))
from engine import run_audit  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
POP_CSV = ROOT / "evidence" / "audit-populations.csv"
SEVERITY_YAML = ROOT / "evidence" / "severity-rules.yaml"
PRIOR_FINDINGS = ROOT / "prior-findings-tracker.csv"
MARKER = "UBI-A7-ADFAFF62AD2E"


def _run_with_prior_findings(outdir: Path):
    """run_audit.run() writes into outdir; evidence-index.csv generation
    requires prior-findings-tracker.csv to already exist at outdir, exactly
    as it does at the real submission root."""
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "prior-findings-tracker.csv").write_text(PRIOR_FINDINGS.read_text())
    return run_audit.run(MARKER, str(POP_CSV), str(SEVERITY_YAML), str(outdir))


def test_evidence_index_is_actually_produced_by_the_documented_build_step(tmp_path):
    result = _run_with_prior_findings(tmp_path)
    assert result["evidence_index_path"] is not None
    assert (tmp_path / "evidence-index.csv").exists()


def test_evidence_index_covers_every_one_of_the_12_tests(tmp_path):
    _run_with_prior_findings(tmp_path)
    with open(tmp_path / "evidence-index.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    test_claims = [r for r in rows if r["report_section"] == "Control testing and verdicts"]
    # 3 fixed methodology/integrity claims are also tagged under some of these
    # sections; specifically count only rows whose claim text is one of the
    # 12 test procedures by checking against the frozen verdicts document.
    import json
    verdicts = json.loads((tmp_path / "evidence-verdicts.json").read_text())
    procedures = {t["procedure"] for t in verdicts["tests"]}
    matched = [r for r in test_claims if r["claim"] in procedures]
    assert len(matched) == 12, f"expected 12 per-test rows, found {len(matched)}"


def test_evidence_index_covers_all_3_prior_findings(tmp_path):
    _run_with_prior_findings(tmp_path)
    with open(tmp_path / "evidence-index.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    prior_rows = [r for r in rows if r["report_section"] == "Prior-finding verification"]
    assert len(prior_rows) == 3


def test_evidence_index_hashes_reproduce_identically_across_two_runs(tmp_path):
    """This is the exact property the brief names explicitly: 'staff rerunning
    with the same marker must obtain identical ... evidence-index hashes.'"""
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    _run_with_prior_findings(out1)
    _run_with_prior_findings(out2)

    with open(out1 / "evidence-index.csv", newline="", encoding="utf-8") as fh:
        rows1 = list(csv.DictReader(fh))
    with open(out2 / "evidence-index.csv", newline="", encoding="utf-8") as fh:
        rows2 = list(csv.DictReader(fh))

    # collection_time_utc is expected to vary run-to-run, exactly like
    # generated_at_utc does elsewhere in this project; strip it before
    # comparing, then confirm every other field is byte-identical.
    def strip_time(rows):
        return [{k: v for k, v in r.items() if k != "collection_time_utc"} for r in rows]

    assert strip_time(rows1) == strip_time(rows2), (
        "evidence-index.csv content differs between two runs with the same marker, "
        "beyond the documented collection_time_utc exception"
    )


def test_evidence_index_claim_ids_are_unique_and_sequential(tmp_path):
    _run_with_prior_findings(tmp_path)
    with open(tmp_path / "evidence-index.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    ids = [r["claim_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate claim_id values found"
    assert ids == sorted(ids), "claim_id values are not in sequential order"


def test_evidence_index_never_silently_fabricates_a_hash_for_narrative_evidence(tmp_path):
    """Rows sourced from evidence-pack.md (no literal CSV record to hash) must
    say so honestly rather than reusing an unrelated file's hash."""
    _run_with_prior_findings(tmp_path)
    with open(tmp_path / "evidence-index.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if r["artifact_path"] == "evidence-pack.md":
            assert r["sha256"] == "n/a-narrative-evidence", (
                f"row {r['claim_id']} cites evidence-pack.md but has a sha256 value that "
                f"implies a hashed file exists: {r['sha256']!r}"
            )
