# Northstar Health Internal Audit Evidence Pack

## Audit context

Audit date: 13-21 July 2026. Scope: the patient-support SaaS production service,
corporate endpoints, identity platform, change process, incident process,
backups, logging, and critical suppliers. The organisation claims alignment to
ISO/IEC 27001:2022 and is preparing for a certification audit.

## Statement of Applicability excerpt, approved 5 January 2026

| Control | Applicable | Status claimed | Owner | SoA justification |
|---|---:|---|---|---|
| A.5.15 | Yes | Implemented | Head of IT | Access governed by role and approval |
| A.5.16 | Yes | Implemented | Head of IT | Identity lifecycle in HR/IdP workflow |
| A.5.18 | Yes | Implemented | CISO | Quarterly access review |
| A.5.19 | Yes | Implemented | Procurement | Supplier security risk process |
| A.5.24 | Yes | Implemented | CISO | Incident roles and preparation |
| A.5.30 | Yes | Implemented | COO | ICT continuity supports business continuity |
| A.6.3 | Yes | Implemented | People Director | Annual awareness and role training |
| A.8.5 | Yes | Implemented | Head of IT | Strong authentication for privileged access |
| A.8.8 | Yes | Implemented | Infrastructure Lead | Vulnerabilities managed to risk SLA |
| A.8.13 | Yes | Implemented | Infrastructure Lead | Backups protected and tested |
| A.8.15 | Yes | Implemented | SOC Lead | Security events logged |
| A.8.32 | Yes | Implemented | Engineering Director | Changes authorized and traceable |

## Policy register

| Document | Version | Approved | Next review | Note |
|---|---|---|---|---|
| Access Control Policy | 3.1 | 3 Feb 2025 | 3 Feb 2026 | Review overdue |
| Supplier Security Standard | 2.0 | 5 Jan 2026 | 5 Jan 2027 | Current |
| Incident Response Plan | 4.2 | 18 Apr 2026 | 18 Apr 2027 | Current |
| Backup Standard | 2.4 | 9 Sep 2024 | 9 Sep 2025 | Review overdue |
| Change Management Policy | 5.0 | 11 Dec 2025 | 11 Dec 2026 | Current |

## Identity export, generated 15 July 2026 10:04 UTC

- 412 active workforce accounts; 26 privileged role assignments.
- Conditional-access policy `Admins-PhishingResistant`: enabled, targets 19 of
  26 privileged assignments. Seven service and emergency accounts are excluded.
- Two excluded emergency accounts authenticated in June using password plus
  SMS. Their documented exception expired 31 March 2026.
- HR termination sample (April-June, 20 records): 18 disabled within 24 hours;
  `n.adamu` disabled after 9 days; `vendor-backup` has no HR record and remains active.

## Access-review tickets

- Q1 review ticket `IAM-4412`, closed 8 April 2026. Reviewer checked finance and
  engineering groups. Evidence attachment lists 207 accounts. Privileged roles
  and service accounts are absent from the sample.
- Q2 review ticket `IAM-5031`, opened 1 July 2026, status "in progress". No
  reviewer sign-off or removal evidence by audit date.

## Supplier evidence

- Critical supplier inventory lists CloudStore, PayBridge, and HelpSphere.
- PayBridge assessment completed 2 February 2026 with two monitored conditions.
- HelpSphere was added 14 May 2026 and can access patient-support attachments.
  Procurement file contains a privacy questionnaire but no security assessment
  or approved risk decision.

## Incident evidence

- IR plan names commander, legal, privacy, communications, and technical leads.
- Exercise ticket `IR-EX-2025-02` is dated 20 November 2025 and tested ransomware.
- The SoA evidence link labels it "2026 annual exercise." File metadata and the
  participant list show it was the November 2025 event.
- A real severity-2 incident on 6 June 2026 used the current escalation roster;
  legal was paged at 42 minutes. Lessons learned were recorded, but one action
  has no owner.

## ICT continuity and backup evidence

- Service RTO: 4 hours; RPO: 1 hour.
- Backup console export generated 14 July 2026: daily database backups encrypted,
  35-day retention, last successful job 14 July 01:10 UTC.
- Restore report supplied as current evidence is dated 22 August 2024. It covers
  a retired database version and achieved a 6 hour 18 minute restore.
- No restore exercise after the 2025 database migration was supplied.

## Awareness evidence

- 2026 general awareness completion: 397 of 412 active workers.
- Fifteen overdue workers include 4 developers and 2 privileged administrators.
- Secure-development role training roster was last completed in October 2024.
- HR states the learning platform migration lost role-training assignments.

## Vulnerability evidence

- Vulnerability SLA: critical internet-facing 7 days; high 30; medium 90.
- Export on 15 July: 2 critical, 14 high, 67 medium open.
- Critical `VULN-882` on public gateway is 19 days old with no approved exception.
- Critical `VULN-901` is 2 days old and has an owner and scheduled emergency change.
- Six high findings exceed 30 days; three have accepted-risk records that expired.

## Logging evidence

- SIEM source list claims 100% production Linux and identity coverage.
- Agent inventory: 48 production Linux servers; 44 reporting in last 24 hours.
- Four silent hosts include the primary billing worker. Monitoring ticket was
  opened 11 days ago and remains unassigned.
- Identity audit logs are retained 90 days. Incident policy requires 180 days.

## Change sample

Twenty changes sampled from April-June 2026:

- 16 standard/normal changes have approval, test evidence, implementation, and closure.
- `CHG-2281` emergency database index change has retrospective approval after 8
  business days; policy requires 5.
- `CHG-2310` firewall emergency change has no linked test evidence.
- `CHG-2344` normal production release was approved by its implementer.
- `CHG-2377` was cancelled and never deployed; it is not a control failure.

## Prior audit report, 12 July 2025

1. `NC-25-01` major: privileged accounts not covered by MFA policy. Due 31 Dec
   2025. Management says closed by the new conditional-access policy.
2. `NC-25-02` minor: restore tests not performed against the production database
   version. Due 31 Mar 2026. Management says closed by "successful daily backups."
3. `OBS-25-03`: supplier inventory missing service owners. Current inventory now
   includes an owner for all three suppliers.

## Interview notes

Head of IT: "All admins have MFA. The seven exclusions are non-human or
emergency identities, so they do not count."  
Infrastructure Lead: "A green backup job is our restore test. We have never
needed to restore the post-migration database."  
SOC Lead: "Four silent agents is within tolerance, but we never formally defined
the tolerance and billing is the one host I would most want."  
Procurement Analyst: "HelpSphere had to launch in May. The privacy questionnaire
was treated as the supplier security review."
