---
id: T-20260716-build-revenue-report
title: Extend daily totals with a TOTAL row and emit the revenue report
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 10
agent: any
parent: (none)
depends_on: [T-20260716-build-category-share, T-20260716-build-daily-totals]
touches_paths:
  - tests/e2e-test-engine/src/build_daily_totals.sh
creates_paths:
  - tests/e2e-test-engine/src/build_daily_totals.sh
  - tests/e2e-test-engine/src/build_report.sh
source_note: cvg-todo.md
created: 2026-07-16T23:11:06Z
tags: ["fixture", "report", "sqlite"]
owner: (none)
priority: P2
severity: feature
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: (none)
source_action_item: (none)
linear_ref: (none)
execution_backend: any
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-07-16T23:16:37Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v1:1f197c76:adab0c3cdaca2aee3ccd3b87ae5c896242845926abd52bd53ced57813abb379b
---

# Extend daily totals with a TOTAL row and emit the revenue report

> **Why:** Diamond apex (T2 + T3 → T4). Deliberately **overlaps T3's blast
> radius** on `build_daily_totals.sh` (listed in both touches_paths and
> creates_paths: the file is created by T3, modified here — the redundant
> creates entry is the sanctioned way to declare a not-yet-existing touch).
> The Manager must serialize this task after T3, never run them in parallel.

---

## Goal

Two changes: (1) extend `tests/e2e-test-engine/src/build_daily_totals.sh` so
`gold_daily_totals` also carries a `TOTAL` row (order_date='TOTAL', revenue =
grand total); (2) create `tests/e2e-test-engine/src/build_report.sh` that
writes `tests/e2e-test-engine/data/report.md` combining daily totals and
category shares.

---

## Context

Runs after T2 (`gold_category_share`) and T3 (`gold_daily_totals`) are done.
Expected after this task: `gold_daily_totals` has 3 rows (2 days + TOTAL
240.00); `data/report.md` contains the string `240.00` and both category
names. `data/` is gitignored, so the report is a generated artifact, not a
tracked file.

---

## Behavior

- **B-1** — GIVEN built gold tables WHEN the extended `build_daily_totals.sh`
  runs THEN `gold_daily_totals` carries a TOTAL row of 240.00 alongside the
  two per-day rows.
- **B-2** — GIVEN built gold tables WHEN `build_report.sh` runs THEN
  `data/report.md` exists and names both categories and the 240.00 total.

---

## Success Criteria

```bash
# eval-1: TOTAL row present and correct, per-day rows intact (3 rows)
eval_1() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_daily_totals.sh" >/dev/null
  tot=$(sqlite3 "$FIX/data/toy.db" "SELECT printf('%.2f', revenue) FROM gold_daily_totals WHERE order_date='TOTAL';")
  rows=$(sqlite3 "$FIX/data/toy.db" "SELECT count(*) FROM gold_daily_totals;")
  [ "$tot" = "240.00" ] && [ "$rows" = "3" ]
}

# eval-2: report.md exists and carries the grand total
eval_2() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_category_share.sh" >/dev/null
  bash "$FIX/src/build_daily_totals.sh" >/dev/null
  bash "$FIX/src/build_report.sh" >/dev/null
  [ -f "$FIX/data/report.md" ] && grep -q '240\.00' "$FIX/data/report.md"
}

# eval-3: report names both categories
eval_3() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_category_share.sh" >/dev/null
  bash "$FIX/src/build_daily_totals.sh" >/dev/null
  bash "$FIX/src/build_report.sh" >/dev/null
  grep -q 'widgets' "$FIX/data/report.md" && grep -q 'gadgets' "$FIX/data/report.md"
}
```

---

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: TOTAL row present and correct, per-day rows intact (3 rows)
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 2
  - id: eval_2
    description: report.md exists and carries the grand total
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 3
  - id: eval_3
    description: report names both categories
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 3

retry_policy:
  max_iterations: 10
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context

agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails, operations]
  produce:
    - code
    - docs
  required_tools: [git, bash, sqlite3]
  timeout_minutes: 15
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit:
    - pass
    - fail
    - retry_with_reason
    - parked_with_context
  backend_metadata: {}
```

---

## Exit Check

```bash
# Final proof-of-done. Returns 0 only when ALL evals pass.
eval_1 && eval_2 && eval_3
```

---

## Rollback Plan

If execution fails mid-task, revert to the pre-task state:

1. **File restore** — `git checkout -- tests/e2e-test-engine/src/build_daily_totals.sh`
   (T3's version is the committed baseline being extended)
2. **State reset** — update task status to `parked` and record `blocked_reason`

---

## Observability Hooks

(none — no runtime observability required)

---

## Anti-Patterns

- **Don't break T3's evals** — the TOTAL row must not disturb the per-day
  rows; T3's evals filter on `order_date LIKE '2026-%'` and must stay green.
- **Don't query silver in the report** — the report reads gold tables only;
  that layering is the point of the diamond.
- **Don't write report.md outside data/** — everything generated lands in the
  gitignored `data/`, keeping the fixture's tracked surface clean.

---

## Do-Not-Touch

Files the executor MUST NOT modify:

- `tests/e2e-test-engine/seed.sh` — seed data is the shared ground truth
- `tests/e2e-test-engine/src/build_gold.sh` — T1's deliverable
- `tests/e2e-test-engine/src/build_category_share.sh` — T2's deliverable
- `tests/e2e-test-engine/evals/` — fixture-level evals are the referee

---

## Open Questions

(none — this task is fully specified)
