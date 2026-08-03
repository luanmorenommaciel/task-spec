---
id: T-20260716-add-quality-check
title: Add a data-quality check script to the e2e fixture
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
  - tests/e2e-test-engine/src/check_quality.sh
source_note: cvg-todo.md
created: 2026-07-16T23:11:06Z
tags: ["fixture", "quality", "sqlite"]
owner: (none)
priority: P2
severity: refactor
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: (none)
source_action_item: (none)
linear_ref: (none)
execution_backend: any
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-07-16T23:16:32Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v1:1f197c76:eb1337fb7bbc93cd55ce7723c1a2b79e3c1a5964148c44c3f57712afc3b56cb0
---

# Add a data-quality check script to the e2e fixture

> **Why:** The diamond's independent fifth task (no dependencies) — it lets
> the Manager prove parallel dispatch: T5 can run alongside T1 from the first
> tick because their blast radii are disjoint.

---

## Goal

Create `tests/e2e-test-engine/src/check_quality.sh` that validates the fixture
database and exits 0 when healthy, 1 when not. It takes an optional db path
argument (default `tests/e2e-test-engine/data/toy.db`) so evals can point it
at a corrupted copy.

Checks: (a) no orphan payments (every `payments.order_id` exists in `orders`),
(b) every order quantity is > 0, (c) every payment amount is > 0.

---

## Context

Seeded db is healthy by construction, so the script must pass on it. The
discriminating evals corrupt a **copy** of the db (orphan payment; zero
quantity) and require the script to fail on it — proving the check actually
checks.

---

## Behavior

- **B-1** — GIVEN the freshly seeded db WHEN `check_quality.sh` runs THEN it
  exits 0.
- **B-2** — GIVEN a copy of the db with planted corruption (orphan payment or
  zero-quantity order) WHEN `check_quality.sh` runs against that copy THEN it
  exits non-zero.

---

## Success Criteria

```bash
# eval-1: healthy seeded db passes the quality check
eval_1() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  bash "$FIX/src/check_quality.sh"
}

# eval-2: corrupted copy (orphan payment) fails the quality check
eval_2() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  cp "$FIX/data/toy.db" "$FIX/data/corrupt.db"
  sqlite3 "$FIX/data/corrupt.db" "INSERT INTO payments VALUES (99, 999, 10.0, 'paid', '2026-07-15T00:00:00Z');"
  if bash "$FIX/src/check_quality.sh" "$FIX/data/corrupt.db"; then return 1; else return 0; fi
}

# eval-3: zero-quantity order in a copy also fails the check
eval_3() {
  FIX=tests/e2e-test-engine
  bash "$FIX/seed.sh" >/dev/null
  cp "$FIX/data/toy.db" "$FIX/data/corrupt.db"
  sqlite3 "$FIX/data/corrupt.db" "UPDATE orders SET quantity = 0 WHERE order_id = 1;"
  if bash "$FIX/src/check_quality.sh" "$FIX/data/corrupt.db"; then return 1; else return 0; fi
}
```

---

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: healthy seeded db passes the quality check
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 2
  - id: eval_2
    description: corrupted copy (orphan payment) fails the quality check
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 2
  - id: eval_3
    description: zero-quantity order in a copy also fails the check
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

- **Don't hardcode "exit 0"** — eval_2/eval_3 exist precisely to refute a
  check that never fails. The queries must actually detect the corruption.
- **Don't modify the real toy.db in checks** — the script is read-only;
  corruption happens only on copies made by the evals.
- **Don't check gold tables** — this task is independent of the T1 chain by
  design; it validates raw/seeded tables only.

---

## Do-Not-Touch

Files the executor MUST NOT modify:

- `tests/e2e-test-engine/seed.sh` — seed data is the shared ground truth
- `tests/e2e-test-engine/evals/` — fixture-level evals are the referee
- `tests/e2e-test-engine/README.md` — control sums documented for humans

---

## Open Questions

(none — this task is fully specified)
