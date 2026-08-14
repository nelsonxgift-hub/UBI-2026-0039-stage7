# Continuity Record

## 1. Previous-stage commit and component reused

Stage 6 (Advanced Stage Project 2, the PeopleFlow Inc. vendor evidence-verification pipeline,
scored 95/100) established the pattern I carried into this stage: a typed evidence collector, a
deterministic check engine, and a CLI orchestrator that emits machine-readable verdicts with
exact source locators.

The Stage 6 final submission commit of record was:
`2a2b16195582e47142fda6803efa05bd23d157a4`

The current Stage 6 repository HEAD, two commits later and documentation-only, was:
`5ab425a060399df6c765039b5d30c7a74449dfa1`

The original Stage 6 UBI-supplied input archive SHA-256 was:
`3e5e6e8f39975da3e07d1b72a54181910e97db74c0d09b43c8553381e6866973`

## 2. Interface consumed and backward-compatible extension

Stage 6's core interface was: load typed evidence, run a fixed set of check functions against
it, and emit a verdict with a locator back to the raw artifact. Stage 7 extends this in three
ways that stay backward-compatible with that shape:

- The check functions become the severity engine's rule evaluators (`engine/severity.py`), now
  driven entirely by an external YAML file instead of being hardcoded per check.
- The evidence input becomes two kinds: CSV populations that support deterministic sampling,
  and narrative evidence that does not.
- The output shape gains an explicit `excluded_records` list with reason codes, making
  exclusions first-class output rather than silently dropped.

## 3. Evidence that prior raw-to-result provenance remains intact

Every one of Stage 7's 12 issued tests (AT-01 through AT-12) carries an exact evidence locator.
`evidence-index.csv` continues Stage 6's practice of a claim-level index with a stated
confidence and an alternative considered.

## 4. Migration record for every incompatible change

The one incompatible change from Stage 6's pattern is that Stage 7 introduces a marker-seeded
sampler, a genuinely new component rather than a replacement, so no migration of Stage 6 logic
was required.

## 5. Component, schema, evidence, or decision record handed to the next stage

I hand forward to Stage 8:

- `nonconformity-register.csv`: 9 nonconformities (6 major, 3 minor), ready for risk-treatment
  planning. Owner and target-closure-date columns are intentionally blank for Stage 8 or
  Northstar Health management to populate.
- `prior-findings-tracker.csv`: the retest methodology for Stage 8 to apply to this stage's
  future prior-finding set.
- `evidence-verdicts.json`: the full verdict set for all 12 controls. Three conform outright
  (A.5.15, A.8.13, A.8.32); the remaining nine do not.
- The severity engine itself (`engine/severity.py`), unchanged in interface.
