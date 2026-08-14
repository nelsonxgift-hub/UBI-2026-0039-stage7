import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit-engine"))
from engine import collector as C  # noqa: E402

POP_CSV = Path(__file__).resolve().parents[1] / "evidence" / "audit-populations.csv"
AUDIT_END = datetime(2026, 7, 21, 23, 59, 59, tzinfo=timezone.utc)


def test_duplicate_record_id_is_flagged_not_dropped():
    records = C.load_populations(str(POP_CSV), AUDIT_END)
    acc004 = [r for r in records if r.population == "access" and r.record_id == "ACC-004"]
    assert len(acc004) == 2, "both duplicate rows must be preserved, not deduplicated away"
    assert acc004[1].is_duplicate_occurrence is True
    assert C.REASON_DUPLICATE_RECORD_ID in acc004[1].reason_codes
    assert acc004[0].is_duplicate_occurrence is False


def test_eligible_records_excludes_duplicate_occurrence():
    records = C.load_populations(str(POP_CSV), AUDIT_END)
    eligible = C.eligible_records(records, "access")
    ids = [r.record_id for r in eligible]
    assert ids.count("ACC-004") == 1, "the sampling frame must not double-count a duplicate"


def test_timezone_offset_is_normalized_to_utc():
    records = C.load_populations(str(POP_CSV), AUDIT_END)
    vul201 = [r for r in records if r.record_id == "VUL-201"][0]
    # VUL-201 is recorded as 2026-06-01T06:00:00-04:00 in the source file, i.e. 10:00 UTC
    assert vul201.event_time_utc == datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)


def test_stale_evidence_is_flagged_by_age_threshold():
    records = C.load_populations(str(POP_CSV), AUDIT_END, stale_after_days=180)
    acc006 = [r for r in records if r.record_id == "ACC-006"][0]
    assert C.REASON_STALE_EVIDENCE in acc006.reason_codes  # 2025-12-12, > 180 days before period end
    acc001 = [r for r in records if r.record_id == "ACC-001"][0]
    assert C.REASON_STALE_EVIDENCE not in acc001.reason_codes  # 2026-07-01, within threshold


def test_malformed_timestamp_is_flagged_not_raised():
    dt = C.parse_utc("not-a-timestamp")
    assert dt is None


def test_missing_timestamp_flagged_when_row_has_blank_event_time(tmp_path):
    p = tmp_path / "pop.csv"
    p.write_text(
        "population,record_id,owner,status,event_time,scope,source_locator\n"
        "access,ACC-900,team,active,,standard,x:1\n"
    )
    records = C.load_populations(str(p), AUDIT_END)
    assert C.REASON_MISSING_TIMESTAMP in records[0].reason_codes


def test_checksum_manifest_detects_positive_and_negative_cases(tmp_path):
    good = tmp_path / "good.txt"
    good.write_text("hello")
    good_hash = hashlib.sha256(b"hello").hexdigest()
    bad_hash = hashlib.sha256(b"tampered").hexdigest()
    mismatches = C.verify_checksum_manifest({str(good): good_hash})
    assert mismatches == [], "a matching hash must not be reported as a mismatch"
    mismatches = C.verify_checksum_manifest({str(good): bad_hash})
    assert len(mismatches) == 1
    assert mismatches[0]["reason_code"] == C.REASON_HASH_MISMATCH


def test_checksum_manifest_missing_file_reported_not_raised(tmp_path):
    missing = tmp_path / "does-not-exist.txt"
    mismatches = C.verify_checksum_manifest({str(missing): "deadbeef"})
    assert len(mismatches) == 1
    assert mismatches[0]["actual"] is None
