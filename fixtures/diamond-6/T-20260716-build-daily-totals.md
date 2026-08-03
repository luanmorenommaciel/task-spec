---
id: T-20260716-build-daily-totals
title: Build gold_daily_totals table in the e2e fixture
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 10
agent: any
parent: (none)
depends_on: [T-20260716-build-gold-daily-revenue]
touches_paths:
  - tests/e2e-test-engine/src/build_daily_totals.sh
creates_paths:
  - tests/e2e-test-engine/src/build_daily_totals.sh
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
signed_off_at: 2026-07-16T23:18:06Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v1:1f197c76:2c2ef18e0a28309f6f4cbeb872d0c446bb81dcfad6c9d9354593158b19b00a8b
---

# Build gold_daily_totals table in the e2e fixture

> **Why:** Right arm of the diamond (T1 → T3 → T4). Collapses the gold table
> to one row per day; T4 later extends this task's script — the deliberate
> `touches_paths` overlap the Manager must serialize.

---

## Goal

Create `tests/e2e-test-engine/src/build_daily_totals.sh` that (re)builds
`gold_daily_totals(order_date, revenue)` in
`tests/e2e-test-engine/data/toy.db`, aggregated from `gold_daily_revenue`.

---

## Context

Depends on T-20260716-build-gold-daily-revenue. Expected rows: 2026-07-14 =
60.00 · 2026-07-15 = 180.00 (2 rows, sum 240.00). Re-runnable (DROP TABLE IF
EXISTS). Keep the script simple — T4 will extend it with a TOTAL row later.

---

## Behavior

- **B-1** — GIVEN a built `gold_daily_revenue` WHEN `build_daily_totals.sh`
  runs THEN `gold_daily_totals` holds one row per order_date with 2026-07-14 =
  60.00 and 2026-07-15 = 180.00.
- **B-2** — GIVEN the built table WHEN revenue is summed THEN it equals 240.00
  (nothing dropped in aggregation).

---

## Success Criteria

```bash
# eval-1: per-day cells are exactly 60.00 and 180.00
eval_1() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_daily_totals.sh" >/dev/null
  d14=$(sqlite3 "$FIX/data/toy.db" "SELECT printf('%.2f', revenue) FROM gold_daily_totals WHERE order_date='2026-07-14';")
  d15=$(sqlite3 "$FIX/data/toy.db" "SELECT printf('%.2f', revenue) FROM gold_daily_totals WHERE order_date='2026-07-15';")
  [ "$d14" = "60.00" ] && [ "$d15" = "180.00" ]
}

# eval-2: exactly one row per day (2 rows)
eval_2() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_daily_totals.sh" >/dev/null
  rows=$(sqlite3 "$FIX/data/toy.db" "SELECT count(*) FROM gold_daily_totals WHERE order_date LIKE '2026-%';")
  [ "$rows" = "2" ]
}

# eval-3: daily totals sum back to the 240.00 control sum
eval_3() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_daily_totals.sh" >/dev/null
  got=$(sqlite3 "$FIX/data/toy.db" "SELECT printf('%.2f', sum(revenue)) FROM gold_daily_totals WHERE order_date LIKE '2026-%';")
  [ "$got" = "240.00" ]
}
```

---

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: per-day cells are exactly 60.00 and 180.00
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 2
  - id: eval_2
    description: exactly one row per day (2 rows)
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 2
  - id: eval_3
    description: daily totals sum back to the 240.00 control sum
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
  task consumes T1's output.
- **Don't add a TOTAL row** — that is T4's extension; adding it here breaks
  eval_2's row count and blurs the two tasks' blast radii.
- **Don't hardcode 60.00/180.00** — derive with GROUP BY order_date.

---

## Do-Not-Touch

Files the executor MUST NOT modify:

- `tests/e2e-test-engine/seed.sh` — seed data is the shared ground truth
- `tests/e2e-test-engine/src/build_gold.sh` — T1's deliverable, consumed as-is
- `tests/e2e-test-engine/evals/` — fixture-level evals are the referee

---

## Open Questions

(none — this task is fully specified)
