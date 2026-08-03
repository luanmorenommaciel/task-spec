# fixtures/diamond-6 — the 6-task diamond backlog

Six real task-specs extracted from the converge repo's e2e analytics fixture
(sqlite-backed, `tests/e2e-test-engine/`). They are the CI fixtures for this
repo: small, fast, dependency-wired, and covering the happy path, the diamond
join, a deliberate blast-radius overlap, and a designed-to-park task.

## The dependency graph

```text
T-20260716-build-gold-daily-revenue ──┬── T-20260716-build-category-share ──┐
        (root: build gold_daily_revenue)│                                   ├── T-20260716-build-revenue-report
                                      └── T-20260716-build-daily-totals ────┘     (join: TOTAL row + report)

T-20260716-add-quality-check        (independent leaf: a data-quality check script)
T-20260716-impossible-control-sum   (independent, DESIGNED TO PARK: asserts a
                                     control sum that can never hold — exercises
                                     the budget-exhaustion path, never dispatched green)
```

The diamond: one root, two parallel mid-tier tasks, one join. Dispatch order is
fully determined by `depends_on`, which is what makes this a useful executor
test bed.

## The deliberate touches_paths overlap

`build-daily-totals` and `build-revenue-report` **both** declare
`tests/e2e-test-engine/src/build_daily_totals.sh` (the report extends the
daily-totals script with a TOTAL row). This is intentional: `taskspec lint`
(the cross-task overlap detector) should flag exactly this pair — a positive
control that the linter fires on real input.

## Provenance and the signature caveat

These files were authored and gated in the **converge** repo. Their
`signed_off_sig: hmac-sha256-v1:1f197c76:…` values were HMAC-stamped with the
origin repo's signing key, which is **not** distributed. In this repo the
signature check therefore degrades to the structural tier (Tier 2) — the
envelope fields are present and well-formed, but the MAC cannot be re-verified
without that key. **That is expected for fixtures**, not corruption: the
key-optional degrade is working as designed. Do not re-stamp them (`gate
--stamp` mutates the envelope); if Tier-1 fixtures are ever needed, regenerate
the whole diamond under a CI-owned key.

## Usage

```bash
taskspec validate fixtures/diamond-6/T-20260716-build-daily-totals.md
taskspec gate fixtures/diamond-6/T-20260716-add-quality-check.md   # read-only, NO --stamp
```

See P0-1 in `TODO.md`: these six are the backlog the multi-engine CI proof
runs green.
