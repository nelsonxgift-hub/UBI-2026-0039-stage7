"""Evidence collector.

Reads the published audit-populations.csv, normalizes timestamps to UTC,
flags duplicate record_ids, flags evidence that is older than the audit-age
threshold, and (when a checksum manifest is supplied) flags files whose
computed SHA-256 does not match the expected value. Every record that is
excluded or flagged keeps its original row and gets a reason_code; nothing is
silently dropped.
"""
from __future__ import annotations
import csv
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


REASON_DUPLICATE_RECORD_ID = "duplicate_record_id"
REASON_STALE_EVIDENCE = "stale_evidence"
REASON_HASH_MISMATCH = "hash_mismatch"
REASON_MISSING_TIMESTAMP = "missing_or_unparseable_timestamp"


@dataclass
class PopulationRecord:
    population: str
    record_id: str
    owner: str
    status: str
    event_time_raw: str
    scope: str
    source_locator: str
    event_time_utc: Optional[datetime] = None
    reason_codes: list = field(default_factory=list)
    is_duplicate_occurrence: bool = False


def parse_utc(raw: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp (with or without an explicit offset) and
    normalize to UTC. Returns None if unparseable."""
    if not raw:
        return None
    try:
        val = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_checksum_manifest(manifest: dict) -> list:
    """manifest: {relative_path: expected_sha256}. Returns a list of dicts
    for mismatches: {"path":..., "expected":..., "actual":..., "reason_code": REASON_HASH_MISMATCH}
    Files that cannot be opened are reported with actual=None."""
    mismatches = []
    for path, expected in manifest.items():
        try:
            actual = sha256_of_file(path)
        except OSError:
            mismatches.append({"path": path, "expected": expected, "actual": None,
                                "reason_code": REASON_HASH_MISMATCH})
            continue
        if actual.lower() != str(expected).lower():
            mismatches.append({"path": path, "expected": expected, "actual": actual,
                                "reason_code": REASON_HASH_MISMATCH})
    return mismatches


def load_populations(csv_path: str, audit_period_end_utc: datetime,
                      stale_after_days: int = 180) -> list:
    """Load audit-populations.csv into PopulationRecord objects. Every row is
    preserved. Duplicate record_ids (same population+record_id) are flagged
    on the 2nd and later occurrence; the first occurrence is kept clean unless
    otherwise flagged. Evidence older than stale_after_days relative to
    audit_period_end_utc is flagged stale. This threshold is a documented
    engine policy (see decision log D-004), not a value handed down in the
    brief."""
    seen_keys = set()
    records = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rec = PopulationRecord(
                population=row["population"],
                record_id=row["record_id"],
                owner=row["owner"],
                status=row["status"],
                event_time_raw=row["event_time"],
                scope=row["scope"],
                source_locator=row["source_locator"],
            )
            key = (rec.population, rec.record_id)
            if key in seen_keys:
                rec.is_duplicate_occurrence = True
                rec.reason_codes.append(REASON_DUPLICATE_RECORD_ID)
            seen_keys.add(key)

            dt = parse_utc(rec.event_time_raw)
            rec.event_time_utc = dt
            if dt is None:
                rec.reason_codes.append(REASON_MISSING_TIMESTAMP)
            else:
                age_days = (audit_period_end_utc - dt).days
                if age_days > stale_after_days:
                    rec.reason_codes.append(REASON_STALE_EVIDENCE)

            records.append(rec)
    return records


def eligible_records(records: list, population: str, scope: Optional[str] = None) -> list:
    """Return records for a population (optionally filtered by scope) that
    are NOT duplicate occurrences. Duplicates are excluded from the eligible
    sampling frame but remain visible in the full record list with their
    reason code."""
    out = []
    for r in records:
        if r.population != population:
            continue
        if r.is_duplicate_occurrence:
            continue
        if scope is not None and r.scope != scope:
            continue
        out.append(r)
    return out
