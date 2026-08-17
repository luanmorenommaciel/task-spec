---
id: T-20260716-build-category-share
title: Build gold_category_share table in the e2e fixture
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 10
agent: any
parent: (none)
depends_on: [T-20260716-build-gold-daily-revenue]
touches_paths: []
creates_paths:
  - tests/e2e-test-engine/src/build_category_share.sh
source_note: cvg-todo.md
created: 2026-07-16T23:11:06Z
tags: ["fixture", "gold", "sqlite"]
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
signed_off_at: 2026-07-16T23:16:33Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v1:1f197c76:c55f12b02d55d77df8cf7e9e50ccac1beb18ffeee0949c5c6657dc47e06cb5ef
---

# Build gold_category_share table in the e2e fixture

> **Why:** Left arm of the diamond (T1 → T2 → T4). Aggregates the gold table
> by category with percentage shares, exercising a task that consumes another
> task's output.

---

## Goal

Create `tests/e2e-test-engine/src/build_category_share.sh` that (re)builds
`gold_category_share(category, revenue, share_pct)` in
`tests/e2e-test-engine/data/toy.db`, aggregated from `gold_daily_revenue`.

---

## Context

Depends on T-20260716-build-gold-daily-revenue: `gold_daily_revenue` must be
built first (its script exists once that task is done). Expected: widgets
120.00 / 50.00 · gadgets 120.00 / 50.00. `share_pct` = category revenue ÷
total × 100, rounded to 2 decimals. Re-runnable (DROP TABLE IF EXISTS).

---

## Behavior

- **B-1** — GIVEN a built `gold_daily_revenue` WHEN `build_category_share.sh`
  runs THEN `gold_category_share` holds one row per category (2 rows) with
  widgets = 120.00 revenue and 50.00 share_pct.
- **B-2** — GIVEN the built table WHEN shares are summed THEN they total
  100.00 (no category dropped, no rounding drift).

---

## Success Criteria

```bash
# eval-1: widgets row is exactly 120.00 revenue / 50.00 share
eval_1() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_category_share.sh" >/dev/null
  got=$(sqlite3 "$FIX/data/toy.db" "SELECT printf('%.2f|%.2f', revenue, share_pct) FROM gold_category_share WHERE category='widgets';")
  [ "$got" = "120.00|50.00" ]
}

# eval-2: exactly one row per category
eval_2() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_category_share.sh" >/dev/null
  rows=$(sqlite3 "$FIX/data/toy.db" "SELECT count(*) FROM gold_category_share;")
  [ "$rows" = "2" ]
}

# eval-3: shares sum to 100.00
eval_3() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_category_share.sh" >/dev/null
  got=$(sqlite3 "$FIX/data/toy.db" "SELECT printf('%.2f', sum(share_pct)) FROM gold_category_share;")
  [ "$got" = "100.00" ]
}
```

---

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: widgets row is exactly 120.00 revenue / 50.00 share
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 2
  - id: eval_2
    description: exactly one row per category
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 2
  - id: eval_3
    description: shares sum to 100.00
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 2

retry_policy:
  max_iterations: 10
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context

agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails, operations]
  produce:
    - code
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

(none — this task is append-only or additive with no destructive changes)

---

## Observability Hooks

(none — no runtime observability required)

---

## Anti-Patterns

- **Don't recompute from silver** — aggregate from `gold_daily_revenue`; this
  task exists to consume T1's output, not to duplicate its logic.
- **Don't hardcode 120.00/50.00** — derive with GROUP BY + a total subquery.
- **Don't build gold_daily_revenue here** — that is T1's job; call its script
  only in evals, never re-implement it.

---

## Do-Not-Touch

Files the executor MUST NOT modify:

- `tests/e2e-test-engine/seed.sh` — seed data is the shared ground truth
- `tests/e2e-test-engine/src/build_gold.sh` — T1's deliverable, consumed as-is
- `tests/e2e-test-engine/evals/` — fixture-level evals are the referee

---

## Open Questions

(none — this task is fully specified)
