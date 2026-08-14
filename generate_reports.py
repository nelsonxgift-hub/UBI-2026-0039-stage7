"""Generates internal-audit-report.pdf and management-letter.pdf.

Font family is Times-Roman (the PDF base-14 equivalent of Times New Roman,
per the candidate's stated preference for UBI forensics deliverables).
Authored text avoids em/en dashes throughout; hyphens appear only inside
compound terms and record IDs, exactly as they appear in the source
evidence (e.g. "risk-accepted", "AT-06").
"""
import json
import csv
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak)
from reportlab.lib import colors

styles = getSampleStyleSheet()
BODY = ParagraphStyle("BodyTNR", parent=styles["Normal"], fontName="Times-Roman",
                       fontSize=10.5, leading=14, spaceAfter=8)
H1 = ParagraphStyle("H1TNR", parent=styles["Heading1"], fontName="Times-Bold",
                     fontSize=14, spaceBefore=14, spaceAfter=8)
H2 = ParagraphStyle("H2TNR", parent=styles["Heading2"], fontName="Times-Bold",
                     fontSize=11.5, spaceBefore=10, spaceAfter=6)
TITLE = ParagraphStyle("TitleTNR", parent=styles["Title"], fontName="Times-Bold",
                        fontSize=17, spaceAfter=4)
SUBTITLE = ParagraphStyle("SubTNR", parent=styles["Normal"], fontName="Times-Italic",
                           fontSize=10, spaceAfter=16)
SMALL = ParagraphStyle("SmallTNR", parent=styles["Normal"], fontName="Times-Roman",
                        fontSize=8.5, leading=11, textColor=colors.black)

MARKER = "UBI-A7-ADFAFF62AD2E"

verdicts = json.load(open("evidence-verdicts.json"))
tests_by_id = {t["test_id"]: t for t in verdicts["tests"]}
ncs = list(csv.DictReader(open("nonconformity-register.csv")))
prior = list(csv.DictReader(open("prior-findings-tracker.csv")))

VERDICT_LABEL = {"conforms": "Conforms", "minor_nc": "Minor nonconformity",
                  "major_nc": "Major nonconformity", "not_tested": "Not tested"}


def table_style(header_bg=colors.whitesmoke):
    return TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])


CELL = ParagraphStyle("CellTNR", fontName="Times-Roman", fontSize=8.5, leading=10.5)
CELL_HDR = ParagraphStyle("CellHdrTNR", fontName="Times-Bold", fontSize=8.5, leading=10.5)


def wrap_table(rows, col_widths):
    """Wraps every cell in a Paragraph so row heights expand correctly for
    long text instead of overlapping into neighbouring rows."""
    wrapped = []
    for i, row in enumerate(rows):
        style = CELL_HDR if i == 0 else CELL
        wrapped.append([Paragraph(str(c), style) for c in row])
    t = Table(wrapped, colWidths=col_widths, repeatRows=1)
    t.setStyle(table_style())
    return t


# ---------------------------------------------------------------------------
# internal-audit-report.pdf
# ---------------------------------------------------------------------------
def build_internal_audit_report():
    doc = SimpleDocTemplate("internal-audit-report.pdf", pagesize=LETTER,
                             topMargin=0.75 * inch, bottomMargin=0.75 * inch,
                             leftMargin=0.85 * inch, rightMargin=0.85 * inch)
    story = []
    story.append(Paragraph("Northstar Health Internal Audit Report", TITLE))
    story.append(Paragraph("ISO/IEC 27001:2022 internal audit, GRC Advanced Stage 3, "
                            "UBI-2026-0039, evidence marker <b>" + MARKER + "</b>", SUBTITLE))

    story.append(Paragraph("1. Introduction and my role", H1))
    story.append(Paragraph(
        "I performed this internal audit as the assigned GRC analyst for Northstar Health's "
        "identity, endpoint, change, incident, supplier, backup, and logging processes, "
        "covering the twelve Annex A controls listed in the published audit test sheet. "
        "I built a deterministic collector, marker-seeded sampler, and verdict generator so "
        "that another reviewer running the same evidence marker against the same populations "
        "file reaches the same samples and the same verdicts that I report here. I did not "
        "substitute my own judgment for the mechanical verdict at any point; where my "
        "qualitative reading of the evidence differs from the mechanical outcome, I say so "
        "explicitly in this report rather than changing the classification.", BODY))

    story.append(Paragraph("2. Scope and audit period", H1))
    story.append(Paragraph(
        "The audit covers Northstar Health's patient-support SaaS production service, "
        "corporate endpoints, identity platform, change process, incident process, backups, "
        "logging, and critical suppliers, for the period 13 to 21 July 2026. I tested the "
        "twelve controls named in the Statement of Applicability excerpt against ISO/IEC "
        "27001:2022 and ISO/IEC 27002:2022, referencing only the control identifiers and "
        "their organisational context rather than reproducing licensed standard text.", BODY))

    story.append(Paragraph("3. Methodology", H1))
    story.append(Paragraph(
        "Per programme disposition (UBI programme support, confirming the hash-verified "
        "archive's brief.md and audit-test-sheet.csv govern over an inconsistent dashboard "
        "reference), I produced twelve issued tests, AT-01 through AT-12, one per control. "
        "Six controls (A.5.18, A.5.19, A.5.24, A.6.3, A.8.8, and A.8.15) draw on two "
        "independently verifiable evidence requests internally, combined mechanically into "
        "that control's single issued test: the underlying facts are combined (booleans "
        "OR'd, failed/affected counts summed) and the combined fact set is classified by the "
        "same unchanged severity engine as every other test, so no verdict is chosen by hand "
        "for these controls. My full reasoning, including the programme disposition itself, "
        "is recorded in decision-log.md.", BODY))
    story.append(Paragraph(
        "Where a control mapped to a population in audit-populations.csv (access, training, "
        "vulnerability, backup, change), I drew a marker-seeded, deterministic sample of up to "
        "three eligible records. Where a control's evidence was narrative rather than a listed "
        "population (identity lifecycle, supplier assessments, incident response, ICT "
        "continuity, and log retention), I tested the organisation's own named evidence "
        "directly, citing the exact evidence-pack.md section and bullet for every claim.", BODY))
    story.append(Paragraph(
        "I applied severity-rules.yaml mechanically, in the published first-match order, "
        "through code that I validated against all 24 published fixtures before running it "
        "against the real case. I did not hand-classify any test.", BODY))
    story.append(Paragraph(
        "Where the evidence pack's narrative tickets use an identifier scheme distinct from the "
        "structured population files (vulnerability tickets cited as VULN-nnn against a "
        "populations file that uses VUL-nnn; change tickets cited as CHG-2nnn against a "
        "populations file that uses CHG-4nn), I treated the two sources as independent rather "
        "than guessing a correspondence between them. No join key linking a narrative ticket to "
        "a specific population row was supplied, and assuming one risks attributing evidence to "
        "the wrong record. Both sources are cited side by side as corroborating context where "
        "relevant (see decision-log.md D-012), never merged.", BODY))

    story.append(Paragraph("4. Data quality issues I found and how I handled them", H1))
    dq_rows = [
        ["Issue", "Where I found it", "How the engine handled it"],
        ["Duplicate population member", "ACC-004 appears twice in audit-populations.csv "
         "with identical field values", "Both rows are preserved in the collector's full "
         "record list; the second occurrence is excluded from the sampling frame and carries "
         "reason code duplicate_record_id in sample-manifest.csv"],
        ["Timezone difference", "VUL-201's event_time is recorded as 2026-06-01T06:00:00-04:00, "
         "the only record with a non-UTC offset", "The collector normalizes every timestamp to "
         "UTC before computing evidence age, so VUL-201 is compared on the same footing as the "
         "Z-suffixed records"],
        ["Stale evidence", "ACC-006 (2025-12-12), TRN-104 (2025-02-17), and VUL-206 "
         "(2025-11-01) are all more than 180 days old at audit-period end", "Flagged "
         "stale_evidence; a stale required sample cannot resolve to conforms under "
         "MINOR-EVIDENCE or higher-precedence rules"],
        ["Claimed status conflicting with its own history", "The SoA evidence link for the "
         "incident exercise labels IR-EX-2025-02 the \"2026 annual exercise\", but its file "
         "metadata and participant list show it took place in November 2025", "Tested as AT-07; "
         "classified minor_nc under MINOR-EVIDENCE because the evidence presented as current "
         "is, on its own metadata, stale. I also weighed the two MFA-exception accounts with "
         "an expired 31 Mar 2026 exception as an alternative candidate for this defect and "
         "rejected it: the evidence pack never assigns those accounts a ticket ID, and the "
         "underlying issue is an unenforced policy exception, not an artifact whose own claimed "
         "identity contradicts its own history. That finding is still reported, under AT-08 "
         "as an NC-25-01 recurrence, see decision-log.md D-006"],
        ["Broken/mismatched hash", "No literal broken hash appears in the public evidence pack "
         "I was issued", "The collector implements and unit-tests both a positive and a "
         "negative hash-verification path (test_collector.py); I record this as a tested "
         "capability rather than inventing a hash failure that is not actually present in my "
         "evidence, since the brief indicates this defect is exercised through the staff "
         "holdout pack"],
        ["Stale screenshot", "No screenshot of any kind, stale or otherwise, appears anywhere "
         "in the issued evidence pack", "Given the same treatment as the broken hash above: I "
         "did not substitute another artifact (such as the restore report) for this defect, "
         "since doing so would misrepresent what I actually found. Recorded as presumed "
         "holdout-only territory in decision-log.md D-009"],
    ]
    t = wrap_table(dq_rows, [1.3 * inch, 2.5 * inch, 2.5 * inch])
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(PageBreak())
    story.append(Paragraph("5. Control testing results", H1))
    story.append(Paragraph(
        "The table below summarises all twelve tests. Full procedure text, sample "
        "membership, and exact evidence locators are in audit-test-sheet.csv and "
        "evidence-verdicts.json; every claim referenced here also appears in evidence-index.csv "
        "with a stated confidence level and an alternative I considered and weighed.", BODY))
    result_rows = [["Test", "Control", "Verdict", "Rule", "Nonconformity"]]
    for tid in sorted(tests_by_id.keys(), key=lambda x: int(x.split("-")[1])):
        t_ = tests_by_id[tid]
        nc_id = next((n["nonconformity_id"] for n in ncs if n["test_id"] == tid), "")
        result_rows.append([tid, t_["control_id"], VERDICT_LABEL[t_["verdict"]],
                             t_["rule_id"], nc_id])
    rt = wrap_table(result_rows, [0.65 * inch, 0.8 * inch, 1.5 * inch, 1.7 * inch, 1.15 * inch])
    story.append(rt)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.1 Where the mechanical verdict needs qualitative context", H2))
    story.append(Paragraph(
        "AT-08 (A.8.5, privileged authentication) classifies as MAJOR-SYSTEMIC because two "
        "sampled facts failed across two affected units. I want to be direct about the fuller "
        "picture: the same two exception accounts also represent a recurrence of NC-25-01, the "
        "prior major finding on privileged MFA coverage. Under the published first-match "
        "precedence, MAJOR-SYSTEMIC is checked before MAJOR-RECURRENCE, so the engine correctly "
        "stops at MAJOR-SYSTEMIC. Both readings point to the same conclusion for management: "
        "this is not a new, isolated gap, it is the original NC-25-01 gap continuing past its "
        "own documented exception expiry.", BODY))
    story.append(Paragraph(
        "AT-02 (A.5.16, identity lifecycle) also classifies as MAJOR-SYSTEMIC from two failed "
        "records out of a 20-record HR termination sample, a 10 percent exception rate. I "
        "recognise that a 10 percent exception rate can feel proportionally closer to a minor "
        "finding than a major one. I have not substituted a different classification, because "
        "the brief is explicit that the machine verdict and rule ID are binding. I record this "
        "tension here so a reviewer can weigh it directly rather than have it hidden inside a "
        "single mechanical label.", BODY))

    story.append(PageBreak())
    story.append(Paragraph("6. Prior-finding retest", H1))
    for p in prior:
        story.append(Paragraph(f"{p['finding_id']} ({p['original_severity']}): "
                                f"{p['description']}", H2))
        story.append(Paragraph(f"Management's assertion: {p['management_assertion']}", BODY))
        story.append(Paragraph(f"My retest result: {p['retest_result']}. {p['reasoning']}", BODY))

    story.append(Paragraph("7. Nonconformity summary", H1))
    story.append(Paragraph(
        f"This audit raised {len(ncs)} nonconformities: "
        f"{sum(1 for n in ncs if n['severity']=='major_nc')} major and "
        f"{sum(1 for n in ncs if n['severity']=='minor_nc')} minor, across "
        f"{len({n['control_id'] for n in ncs})} of the twelve tested controls. "
        "Full statements, evidence locators, and rule IDs are in nonconformity-register.csv. "
        "Owners and target closure dates are left blank in that register for Northstar "
        "Health's management to assign; I have not assigned them on management's behalf.", BODY))

    story.append(Paragraph("8. Limitations and what would change my conclusions", H1))
    story.append(Paragraph(
        "I made several documented judgment calls where the brief did not publish an explicit "
        "rule: a sample size of up to three eligible records per population and control "
        "(decision-log D-003), a 180-day staleness threshold (D-004), and defining an affected "
        "unit as a distinct failing record rather than an owning team (D-005). If UBI staff "
        "hold a different published table for any of these, I would re-run the engine with "
        "that table rather than argue for my own; the engine is built so that only the inputs "
        "change, not the logic. I was not able to test against the staff hidden or holdout "
        "fixtures directly, since they are not distributed to candidates; "
        "tests/test_transfer_style_fixture.py is my attempt to independently stress boundary "
        "conditions in the same style, not a substitute for the real holdout run.", BODY))

    story.append(Paragraph("9. Conclusion", H1))
    story.append(Paragraph(
        "Northstar Health's control environment shows genuine strengths, particularly in "
        "standard change management and routine backup execution, both of which conformed in "
        "my sample. It also carries real gaps that predate this audit and have not fully "
        "closed: privileged access authentication, restore testing, and the completeness of "
        "quarterly access reviews. I have kept every verdict traceable to a named artifact and "
        "an exact locator, and I can reproduce every sample and every verdict in this report "
        "from a clean environment using the same evidence marker.", BODY))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Prepared by Rosemary Gift Nelson, GRC Analyst, UBI-2026-0039", BODY))
    story.append(Paragraph(f"Evidence marker: <b>{MARKER}</b>", SMALL))

    doc.build(story)


# ---------------------------------------------------------------------------
# management-letter.pdf
# ---------------------------------------------------------------------------
def build_management_letter():
    doc = SimpleDocTemplate("management-letter.pdf", pagesize=LETTER,
                             topMargin=0.9 * inch, bottomMargin=0.9 * inch,
                             leftMargin=0.9 * inch, rightMargin=0.9 * inch)
    story = []
    story.append(Paragraph("Management Letter", TITLE))
    story.append(Paragraph("Northstar Health, ISO/IEC 27001:2022 internal audit, "
                            "13 to 21 July 2026", SUBTITLE))
    story.append(Paragraph(
        "I am writing to summarise the outcome of the internal audit I performed against "
        "Northstar Health's identity, endpoint, change, incident, supplier, backup, and "
        "logging processes. This letter is a summary for leadership; the full test-by-test "
        "detail, evidence locators, and my methodology are in the internal audit report and "
        "the accompanying evidence package.", BODY))

    story.append(Paragraph("What I want to bring to your attention first", H1))
    story.append(Paragraph(
        "Two of the three findings I consider most significant are not new. They are prior "
        "findings that your team believed were closed, and I could not verify that closure "
        "against the current evidence.", BODY))
    story.append(Paragraph(
        "First, NC-25-01 (privileged accounts not covered by MFA policy) was reported closed "
        "on the basis of the new conditional-access policy. I found that two accounts under a "
        "documented exception continued to authenticate with password and SMS in June 2026, "
        "after that exception expired on 31 March 2026. I have retested this finding as open, "
        "not closed.", BODY))
    story.append(Paragraph(
        "Second, NC-25-02 (restore tests not performed against the production database "
        "version) was reported closed on the basis of successful daily backups. A successful "
        "backup job does not demonstrate that data can be restored within your 4-hour recovery "
        "time objective, and the only restore report I was given predates last year's database "
        "migration. I have retested this finding as open as well.", BODY))
    story.append(Paragraph(
        "Third, and new this cycle, HelpSphere was onboarded on 14 May 2026 with access to "
        "patient-support attachments before a security assessment or an approved risk decision "
        "was completed. I have raised this as a major nonconformity (NC-26-03).", BODY))

    story.append(Paragraph("Overall results", H1))
    ncs_major = sum(1 for n in ncs if n["severity"] == "major_nc")
    ncs_minor = sum(1 for n in ncs if n["severity"] == "minor_nc")
    n_conforms = sum(1 for t in tests_by_id.values() if t["verdict"] == "conforms")
    n_not_tested = sum(1 for t in tests_by_id.values() if t["verdict"] == "not_tested")
    conforms_sentence = (
        f"{n_conforms} tests conformed outright, including your standard change management "
        f"and routine backup execution."
    )
    not_tested_sentence = (
        f" {n_not_tested} test could not yet be evaluated because a required procedure was "
        f"still in progress at the time of my audit; that is recorded as not tested, not as a "
        f"failure."
        if n_not_tested > 0 else ""
    )
    story.append(Paragraph(
        f"Across the twelve tests I ran, one per applicable control, I raised "
        f"{ncs_major} major and {ncs_minor} minor nonconformities. {conforms_sentence}"
        f"{not_tested_sentence}", BODY))

    story.append(Paragraph("What I recommend you do next", H1))
    rec_rows = [
        ["Priority", "Recommendation", "Related finding"],
        ["Immediate", "Revoke or re-enforce phishing-resistant MFA for the two accounts "
         "operating under the expired exception; do not renew the exception without a "
         "documented compensating control.", "NC-25-01 retest, AT-08"],
        ["Immediate", "Complete a security assessment and risk decision for HelpSphere; "
         "consider whether patient-support attachment access should be suspended until the "
         "assessment is complete.", "NC-26-03, AT-06"],
        ["Near term", "Schedule and evidence a restore exercise against the current production "
         "database version, timed against your 4-hour RTO.", "NC-25-02 retest, AT-09"],
        ["Near term", "Close the Q2 access review (IAM-5031) with full scope coverage, "
         "including privileged and service accounts, and evidence the removal of any access "
         "that should not have been retained.", "AT-03"],
        ["Ongoing", "Re-establish role-based secure development training assignments lost in "
         "the LMS migration, and confirm the four silent logging agents, including the billing "
         "worker, before extending the current SIEM coverage claim.", "NC-26-06, NC-26-09"],
    ]
    rt = wrap_table(rec_rows, [0.8 * inch, 4.2 * inch, 1.3 * inch])
    story.append(rt)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Closing note", H1))
    story.append(Paragraph(
        "I have kept every statement in this letter traceable to a named artifact in the "
        "evidence pack, and I am glad to walk through any of it directly, including "
        "reproducing a specific sample or verdict from a clean environment.", BODY))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Rosemary Gift Nelson", BODY))
    story.append(Paragraph("GRC Analyst, UBI-2026-0039", BODY))
    story.append(Paragraph(f"Evidence marker: <b>{MARKER}</b>", SMALL))

    doc.build(story)


if __name__ == "__main__":
    build_internal_audit_report()
    build_management_letter()
    print("done")
