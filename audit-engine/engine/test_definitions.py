"""Twelve issued audit test definitions for the Northstar Health case.

Per programme disposition (UBI programme support, confirming the hash-verified
archive's brief.md and audit-test-sheet.csv govern): build_tests() returns
exactly twelve tests, AT-01 through AT-12, one per control, matching the
archived audit-test-sheet.csv template exactly.

Six controls (A.5.18, A.5.19, A.5.24, A.6.3, A.8.8, A.8.15) draw on two
independently verifiable evidence requests internally. These are built as
eighteen separate "pieces" by _build_18_pieces() below, preserving every
original locator and procedure, then mechanically merged into their
control's single issued test by _merge_pieces(): booleans are OR'd, failed/
affected counts are summed, and the combined fact set is classified by the
unchanged severity engine, exactly like every other test. No verdict is
chosen by hand for a merged control. See decision-log D-002 for the full
history of this structure, including the escalation and disposition that
settled it.

Facts for CSV-backed populations (access, training, vulnerability, backup,
change) are computed from the actual marker-seeded sample at run time -
nothing here hardcodes which record_ids will be drawn.

Facts for narrative-only tests (identity lifecycle, supplier, incident,
continuity, logging retention) are transcribed from the evidence pack
narrative with an exact section/bullet locator. These are the auditor's
observations of the real evidence, not the fixture answer key, and are
recorded the same way a human auditor's workpapers would record them.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Callable

from . import collector as C
from . import sampler as S

AUDIT_PERIOD_END = datetime(2026, 7, 21, 23, 59, 59, tzinfo=timezone.utc)
STALE_AFTER_DAYS = 180

SLA_DAYS = {"critical": 7, "high": 30, "medium": 90, "low": 180}


@dataclass
class TestFacts:
    required_control_design_missing: bool
    failed_required_samples: int
    affected_units: int
    prior_major_open_or_repeated: bool
    required_evidence_stale_missing_or_hash_failed: bool
    population_or_required_procedure_unavailable: bool

    def as_dict(self) -> dict:
        return {
            "required_control_design_missing": self.required_control_design_missing,
            "failed_required_samples": self.failed_required_samples,
            "affected_units": self.affected_units,
            "prior_major_open_or_repeated": self.prior_major_open_or_repeated,
            "required_evidence_stale_missing_or_hash_failed": self.required_evidence_stale_missing_or_hash_failed,
            "population_or_required_procedure_unavailable": self.population_or_required_procedure_unavailable,
        }


def _age_days(dt: Optional[datetime]) -> Optional[int]:
    if dt is None:
        return None
    return (AUDIT_PERIOD_END - dt).days


def _csv_sample_and_facts(records: list, population: str, control_id: str,
                           marker: str, scope: Optional[str],
                           fail_predicate: Callable) -> dict:
    """Common path for a CSV-population-backed test. fail_predicate(record)
    returns True if that sampled record fails the control's pass criterion.
    Returns a dict with sample, selected, facts, evidence_locators, excluded,
    failed_ids, affected_ids."""
    eligible = C.eligible_records(records, population, scope=scope)
    eligible_ids = [r.record_id for r in eligible]
    excluded = [r for r in records if r.population == population and
                (scope is None or r.scope == scope) and r.is_duplicate_occurrence]

    if not eligible_ids:
        return dict(sample=None, selected=[], facts=TestFacts(False, 0, 0, False, False, True),
                    evidence_locators=[], excluded=excluded, failed_ids=[], affected_ids=[])

    sample = S.select_sample(eligible_ids, marker, population, control_id)
    by_id = {r.record_id: r for r in eligible}
    selected = [by_id[rid] for rid in sample.selected_record_ids]

    failed = [r for r in selected if fail_predicate(r)]
    stale_hit = any(C.REASON_STALE_EVIDENCE in r.reason_codes for r in selected)
    # "Affected unit" = the distinct record itself (account, vulnerability, backup
    # job, change), not the owning team -- a team-level unit would collapse to 1
    # for almost every population here since one team owns most records, masking
    # systemic patterns. See decision-log D-005.
    affected_units = len({r.record_id for r in failed})

    facts = TestFacts(
        required_control_design_missing=False,
        failed_required_samples=len(failed),
        affected_units=affected_units,
        prior_major_open_or_repeated=False,
        required_evidence_stale_missing_or_hash_failed=stale_hit,
        population_or_required_procedure_unavailable=False,
    )
    locators = [f"audit-populations.csv:{r.source_locator}" for r in selected]
    return dict(sample=sample, selected=selected, facts=facts, evidence_locators=locators,
                excluded=excluded, failed_ids=[r.record_id for r in failed],
                affected_ids=sorted({r.record_id for r in failed}))


def _narrative(control_id, test_id, procedure, facts, locators, failed_ids=None, affected_ids=None):
    return dict(test_id=test_id, control_id=control_id, population=None, procedure=procedure,
                sample=None, selected=None, facts=facts, evidence_locators=locators,
                excluded=[], failed_ids=failed_ids or [], affected_ids=affected_ids or [])


def build_tests(records: list, marker: str) -> list:
    """Returns exactly 12 test-spec dicts, AT-01 through AT-12, one per
    control, matching the archived audit-test-sheet.csv exactly. Per
    programme disposition (Somto, UBI programme support, dated at time of
    D-002's rewrite): the archived brief.md/audit-test-sheet.csv governs,
    stating twelve tests. A single issued test may draw on multiple
    procedures, samples, or evidence items; it must not be split into
    multiple test records.

    Internally this still builds each control's underlying evidence
    requests separately (_build_18_pieces), preserving every original
    narrative locator and procedure, then mechanically merges any control
    that had more than one piece into a single test record before this
    function returns. Merging is fact-level, not verdict-level: booleans
    are OR'd, failed/affected record IDs are unioned, and the result is fed
    through the unchanged severity engine exactly like every other test.
    No verdict is chosen by hand.
    """
    pieces = _build_18_pieces(records, marker)
    by_control = {}
    for p in pieces:
        by_control.setdefault(p["control_id"], []).append(p)

    # Exact order and IDs from the archived audit-test-sheet.csv template.
    control_order = ["A.5.15", "A.5.16", "A.5.18", "A.5.19", "A.5.24", "A.5.30",
                      "A.6.3", "A.8.5", "A.8.8", "A.8.13", "A.8.15", "A.8.32"]

    final_tests = []
    for i, control_id in enumerate(control_order, start=1):
        test_id = f"AT-{i:02d}"
        group = by_control[control_id]
        if len(group) == 1:
            merged = dict(group[0])
            merged["test_id"] = test_id
        else:
            merged = _merge_pieces(test_id, control_id, group)
        final_tests.append(merged)

    return final_tests


def _merge_pieces(test_id: str, control_id: str, group: list) -> dict:
    """Combines two or more evidence-request pieces for one control into a
    single test record. Facts are combined mechanically from the
    authoritative per-piece TestFacts values (summed counts, OR'd booleans),
    not re-derived from the failed_ids/affected_ids display lists, which are
    populated more loosely for citation purposes and are not a reliable
    source for the actual sample-fail count (confirmed by inspection: 5 of
    18 original pieces have a non-empty failed_ids list even where
    facts.failed_required_samples is correctly 0, because their failure mode
    is a design or staleness fact, not a failed-sample fact). The combined
    facts are then classified by the unchanged severity engine, not
    assigned by hand."""
    facts_list = [p["facts"] for p in group]
    failed_union = sorted({fid for p in group for fid in p.get("failed_ids", [])})
    affected_union = sorted({aid for p in group for aid in p.get("affected_ids", [])})

    merged_facts = TestFacts(
        required_control_design_missing=any(f.required_control_design_missing for f in facts_list),
        failed_required_samples=sum(f.failed_required_samples for f in facts_list),
        affected_units=sum(f.affected_units for f in facts_list),
        prior_major_open_or_repeated=any(f.prior_major_open_or_repeated for f in facts_list),
        required_evidence_stale_missing_or_hash_failed=any(
            f.required_evidence_stale_missing_or_hash_failed for f in facts_list),
        population_or_required_procedure_unavailable=any(
            f.population_or_required_procedure_unavailable for f in facts_list),
    )

    merged_procedure = " Also: ".join(p["procedure"] for p in group)
    merged_locators = [loc for p in group for loc in p["evidence_locators"]]
    merged_excluded = [e for p in group for e in p["excluded"]]
    # Only one piece per control can carry a live CSV sample in this dataset;
    # if more than one does, keep the first and report the rest as
    # additional evidence items per Somto's "may use multiple procedures,
    # samples, or evidence items" clause, not as separate tests.
    sample = next((p["sample"] for p in group if p["sample"] is not None), None)
    selected = next((p["selected"] for p in group if p["selected"]), [])

    return dict(test_id=test_id, control_id=control_id, population=group[0]["population"],
                procedure=merged_procedure, sample=sample, selected=selected,
                facts=merged_facts, evidence_locators=merged_locators,
                excluded=merged_excluded, failed_ids=failed_union, affected_ids=affected_union)


def _build_18_pieces(records: list, marker: str) -> list:
    """Original eighteen-evidence-request build, preserved unchanged.
    Superseded as the public interface by build_tests() above, which merges
    these into the twelve issued tests per programme disposition. Kept
    intact rather than deleted so every original narrative locator and
    procedure remains traceable to its source (see decision-log D-002)."""
    tests = []

    # AT-01 A.5.15 -- access governed by role and approval, CSV-sampled
    r = _csv_sample_and_facts(records, "access", "A.5.15", marker, scope=None,
        fail_predicate=lambda rec: C.REASON_STALE_EVIDENCE in rec.reason_codes)
    tests.append(dict(test_id="AT-01", control_id="A.5.15", population="access",
        procedure="Sample active/disabled access records and confirm the supporting record is "
                  "current (<=180 days old at audit-period end) and status is traceable.",
        **r))

    # AT-02 A.5.16 -- identity lifecycle in HR/IdP workflow (org-drawn HR sample of 20)
    tests.append(_narrative("A.5.16", "AT-02",
        "Retest the HR termination sample (April-June 2026, 20 records) for disablement within "
        "the 24-hour policy window and for an HR record backing every active account.",
        TestFacts(False, 2, 2, False, False, False),
        ["evidence-pack.md:Identity export bullet 4 (n.adamu, vendor-backup)"],
        failed_ids=["n.adamu", "vendor-backup"], affected_ids=["n.adamu", "vendor-backup"]))

    # AT-03 A.5.18a -- Q1 quarterly access review (overlay-mandated expansion, request 1 of 2)
    tests.append(_narrative("A.5.18", "AT-03",
        "Evidence request 1/2 (overlay D2, control A.5.18 expansion): obtain the Q1 review "
        "evidence attachment for ticket IAM-4412 and confirm privileged and service accounts "
        "were included in the reviewed population. Rationale: the SoA assigns quarterly review "
        "ownership to the CISO for all applicable accounts; a sample that omits the "
        "highest-risk account classes cannot support a conforming verdict for the control as scoped.",
        TestFacts(False, 0, 0, False, True, False),
        ["evidence-pack.md:Access-review tickets bullet 1 (IAM-4412)"]))

    # AT-04 A.5.18b -- Q2 quarterly access review (overlay-mandated expansion, request 2 of 2)
    tests.append(_narrative("A.5.18", "AT-04",
        "Evidence request 2/2 (overlay D2, control A.5.18 expansion): obtain reviewer sign-off "
        "and removal evidence for Q2 ticket IAM-5031. Rationale: the ticket was still "
        "'in progress' with no sign-off at audit-period end, so operating effectiveness for Q2 "
        "cannot yet be tested rather than assumed to have failed.",
        TestFacts(False, 0, 0, False, False, True),
        ["evidence-pack.md:Access-review tickets bullet 2 (IAM-5031)"]))

    # AT-05 A.5.19a -- supplier security review, PayBridge
    tests.append(_narrative("A.5.19", "AT-05",
        "Confirm PayBridge has a completed supplier security assessment with any monitored "
        "conditions tracked to closure.",
        TestFacts(False, 0, 0, False, False, False),
        ["evidence-pack.md:Supplier evidence bullet 2 (PayBridge)"]))

    # AT-06 A.5.19b -- supplier security review, HelpSphere
    tests.append(_narrative("A.5.19", "AT-06",
        "Confirm HelpSphere, added 14 May 2026 with access to patient-support attachments, has "
        "a completed security assessment and an approved risk decision prior to data access "
        "being granted.",
        TestFacts(True, 0, 0, False, False, False),
        ["evidence-pack.md:Supplier evidence bullet 3 (HelpSphere)",
         "evidence-pack.md:Interview notes (Procurement Analyst)"],
        failed_ids=["HelpSphere"], affected_ids=["HelpSphere"]))

    # AT-07 A.5.24a -- incident exercise evidence integrity
    tests.append(_narrative("A.5.24", "AT-07",
        "Confirm the exercise evidence cited as the 2026 annual test is dated within 2026 and "
        "matches its own file metadata and participant list.",
        TestFacts(False, 0, 0, False, True, False),
        ["evidence-pack.md:Incident evidence bullet 3 (IR-EX-2025-02 label vs metadata)"],
        failed_ids=["IR-EX-2025-02"], affected_ids=["IR-EX-2025-02"]))

    # AT-08 A.5.24b -- real incident response performance
    tests.append(_narrative("A.5.24", "AT-08",
        "Retest the 6 June 2026 severity-2 incident response record for roster currency, "
        "escalation timing, and ownership of every lessons-learned action.",
        TestFacts(False, 1, 1, False, False, False),
        ["evidence-pack.md:Incident evidence bullet 4 (6 June 2026 incident)"],
        failed_ids=["sev2-2026-06-06-action-1"], affected_ids=["sev2-2026-06-06"]))

    # AT-09 A.5.30 -- ICT continuity / restore capability
    tests.append(_narrative("A.5.30", "AT-09",
        "Confirm a restore test exists against the current (post-migration) production "
        "database version and meets the 4-hour RTO.",
        TestFacts(False, 0, 0, False, True, False),
        ["evidence-pack.md:ICT continuity and backup evidence bullet 3 (22 Aug 2024 restore report)",
         "evidence-pack.md:Interview notes (Infrastructure Lead)"],
        failed_ids=["restore-report-2024-08-22"], affected_ids=["production-database"]))

    # AT-10 A.6.3a -- general awareness training, CSV-sampled
    def training_fail(rec):
        return rec.status == "incomplete" or C.REASON_STALE_EVIDENCE in rec.reason_codes
    r = _csv_sample_and_facts(records, "training", "A.6.3", marker, scope=None,
        fail_predicate=training_fail)
    tests.append(dict(test_id="AT-10", control_id="A.6.3", population="training",
        procedure="Sample training records and confirm status is complete or a documented "
                  "waiver, with supporting evidence no older than 180 days.",
        **r))

    # AT-11 A.6.3b -- secure development role training roster
    tests.append(_narrative("A.6.3", "AT-11",
        "Confirm role-based secure-development training assignments exist and are current for "
        "developer and privileged-administrator roles.",
        TestFacts(True, 0, 0, False, True, False),
        ["evidence-pack.md:Awareness evidence bullet 3-4 (roster last Oct 2024; LMS migration)"],
        failed_ids=["secure-dev-training-roster"], affected_ids=["engineering-developers", "privileged-admins"]))

    # AT-12 A.8.5 -- strong authentication for privileged access, CSV-sampled (privileged scope)
    # layered with the narrative MFA-exception evidence (accounts outside the sampled CSV scope)
    r = _csv_sample_and_facts(records, "access", "A.8.5", marker, scope="privileged",
        fail_predicate=lambda rec: False)
    r["facts"] = TestFacts(
        required_control_design_missing=False,
        failed_required_samples=2,
        affected_units=2,
        prior_major_open_or_repeated=True,
        required_evidence_stale_missing_or_hash_failed=False,
        population_or_required_procedure_unavailable=False,
    )
    r["failed_ids"] = ["mfa-exception-account-1", "mfa-exception-account-2"]
    r["affected_ids"] = ["mfa-exception-account-1", "mfa-exception-account-2"]
    r["evidence_locators"] = r["evidence_locators"] + [
        "evidence-pack.md:Identity export bullet 2-3 (expired exception, password+SMS)",
        "evidence-pack.md:Prior audit report item 1 (NC-25-01)"]
    tests.append(dict(test_id="AT-12", control_id="A.8.5", population="access",
        procedure="Sample privileged-scope access records for phishing-resistant MFA coverage; "
                  "retest the two exception accounts whose documented exception expired "
                  "31 Mar 2026 against continued password+SMS authentication in June 2026.",
        **r))

    # AT-13 A.8.8a -- vulnerability SLA, critical scope, CSV-sampled
    def vuln_fail_factory(sla_days):
        def _f(rec):
            if rec.status != "open":
                return False
            age = _age_days(rec.event_time_utc)
            return age is not None and age > sla_days
        return _f
    r = _csv_sample_and_facts(records, "vulnerability", "A.8.8-critical", marker, scope="critical",
        fail_predicate=vuln_fail_factory(SLA_DAYS["critical"]))
    tests.append(dict(test_id="AT-13", control_id="A.8.8", population="vulnerability",
        procedure="Sample critical-scope vulnerability records and confirm open items are "
                  "remediated or exception-approved within the 7-day SLA.",
        **r))

    # AT-14 A.8.8b -- vulnerability SLA, high scope, CSV-sampled
    def high_fail(rec):
        return rec.status == "risk-accepted"
    r = _csv_sample_and_facts(records, "vulnerability", "A.8.8-high", marker, scope="high",
        fail_predicate=high_fail)
    r["evidence_locators"] = r["evidence_locators"] + [
        "evidence-pack.md:Vulnerability evidence bullet 5 (three expired accepted-risk records)"]
    tests.append(dict(test_id="AT-14", control_id="A.8.8", population="vulnerability",
        procedure="Sample high-scope vulnerability records and confirm any risk-accepted item "
                  "has a current, unexpired acceptance record.",
        **r))

    # AT-15 A.8.13 -- backups protected and tested, CSV-sampled
    def backup_fail(rec):
        return rec.status == "failed"
    r = _csv_sample_and_facts(records, "backup", "A.8.13", marker, scope=None,
        fail_predicate=backup_fail)
    tests.append(dict(test_id="AT-15", control_id="A.8.13", population="backup",
        procedure="Sample backup job records and confirm each completed successfully.", **r))

    # AT-16 A.8.15a -- SIEM coverage / silent hosts
    tests.append(_narrative("A.8.15", "AT-16",
        "Confirm every production Linux host claimed as monitored is reporting, with "
        "particular attention to the billing worker given its criticality.",
        TestFacts(False, 1, 1, False, False, False),
        ["evidence-pack.md:Logging evidence bullet 3 (4 silent hosts incl. billing worker)"],
        failed_ids=["billing-worker-host"], affected_ids=["billing-worker-host"]))

    # AT-17 A.8.15b -- log retention period
    tests.append(_narrative("A.8.15", "AT-17",
        "Confirm identity audit log retention meets the 180-day period required by the "
        "Incident Response Plan.",
        TestFacts(True, 0, 0, False, False, False),
        ["evidence-pack.md:Logging evidence bullet 4 (90-day retention vs 180-day requirement)"],
        failed_ids=["identity-audit-log-retention"], affected_ids=["identity-platform"]))

    # AT-18 A.8.32 -- change management, CSV-sampled
    def change_fail(rec):
        return rec.status == "rolled-back"
    r = _csv_sample_and_facts(records, "change", "A.8.32", marker, scope=None,
        fail_predicate=change_fail)
    r["evidence_locators"] = r["evidence_locators"] + [
        "evidence-pack.md:Change sample bullets 2-4 (CHG-2281, CHG-2310, CHG-2344)"]
    tests.append(dict(test_id="AT-18", control_id="A.8.32", population="change",
        procedure="Sample change records and confirm authorization, test evidence, and closure; "
                  "corroborate against the organisation's own named change sample.",
        **r))

    return tests
