---
id: T-20260716-build-gold-daily-revenue
title: Build gold_daily_revenue table in the e2e fixture
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 10
agent: any
parent: (none)
depends_on: []
touches_paths: []
creates_paths:
  - tests/e2e-test-engine/src/build_gold.sh
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
signed_off_at: 2026-07-16T23:16:36Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v1:1f197c76:5f9952d26ca7fd4cbd2ab1ddbe0ad88ff0fcc79166a05a7c2c63c607b32ebcd9
---

# Build gold_daily_revenue table in the e2e fixture

> **Why:** The fixture's gold layer is deliberately absent (see
> `tests/e2e-test-engine/evals/red.sh`). This is the root task of the diamond
> backlog: T2/T3/T4 all consume the table this task builds.

---

## Goal

Create `tests/e2e-test-engine/src/build_gold.sh` that (re)builds a
`gold_daily_revenue(order_date, category, revenue)` table in
`tests/e2e-test-engine/data/toy.db` from the existing `silver_orders` view,
counting **paid revenue only**.

---

## Context

Fixture seeded by `tests/e2e-test-engine/seed.sh` (deterministic; control sums
in its README). `silver_orders` carries `is_paid` and `paid_amount`. Expected
gold: 2026-07-14 widgets 20.00 · 2026-07-14 gadgets 40.00 · 2026-07-15 widgets
100.00 · 2026-07-15 gadgets 80.00 — total 240.00. The script must be
re-runnable (DROP TABLE IF EXISTS first).

---

## Behavior

- **B-1** — GIVEN the seeded fixture db WHEN `build_gold.sh` runs THEN
  `gold_daily_revenue` exists and its `revenue` sums to exactly 240.00
  (paid orders only).
- **B-2** — GIVEN the built gold table WHEN queried THEN it holds exactly one
  row per (order_date, category) pair — 4 rows — with 2026-07-14/widgets =
  20.00, and re-running the script leaves the same result (idempotent).

---

## Success Criteria

```bash
# eval-1: build runs and paid-only total is exactly 240.00
eval_1() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  got=$(sqlite3 "$FIX/data/toy.db" "SELECT printf('%.2f', sum(revenue)) FROM gold_daily_revenue;")
  [ "$got" = "240.00" ]
}

# eval-2: grain is date x category — 4 rows, spot-check one cell
eval_2() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  rows=$(sqlite3 "$FIX/data/toy.db" "SELECT count(*) FROM gold_daily_revenue;")
  cell=$(sqlite3 "$FIX/data/toy.db" "SELECT printf('%.2f', revenue) FROM gold_daily_revenue WHERE order_date='2026-07-14' AND category='widgets';")
  [ "$rows" = "4" ] && [ "$cell" = "20.00" ]
}

# eval-3: idempotent — running the build twice changes nothing
eval_3() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  bash "$FIX/src/build_gold.sh" >/dev/null
  got=$(sqlite3 "$FIX/data/toy.db" "SELECT count(*) || '|' || printf('%.2f', sum(revenue)) FROM gold_daily_revenue;")
  [ "$got" = "4|240.00" ]
}
```

---

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: build runs and paid-only total is exactly 240.00
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 2
  - id: eval_2
    description: grain is date x category — 4 rows, spot-check one cell
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 2
  - id: eval_3
    description: idempotent — running the build twice changes nothing
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
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

- **Don't hardcode the revenue values** — the table must be computed from
  `silver_orders`, or the eval is satisfied by a lookup table. Derive with
  GROUP BY.
- **Don't count unpaid orders** — revenue is paid-only (orders 4 and 6 carry
  no payment). Filter on `is_paid = 1`.
- **Don't modify the seed data** — the control sums are load-bearing for every
  other fixture task. Build downstream of silver only.

---

## Do-Not-Touch

Files the executor MUST NOT modify:

- `tests/e2e-test-engine/seed.sh` — seed data is the shared ground truth
- `tests/e2e-test-engine/evals/` — fixture-level evals are the referee
- `tests/e2e-test-engine/README.md` — control sums documented for humans

---

## Open Questions

(none — this task is fully specified)
