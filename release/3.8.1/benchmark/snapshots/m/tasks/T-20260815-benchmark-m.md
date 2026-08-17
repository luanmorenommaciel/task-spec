---
id: T-20260815-benchmark-m
title: "Repair dependency readiness and cycle diagnostics"
status: ready
format_version: 3
profile: standard
effort: M
budget_iterations: 8
agent: any
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: [work/m/task_graph.py]
creates_paths: []
source_note: "Task-Spec 3.8.1 frozen engine benchmark"
created: "2026-08-15T00:00:00Z"
tags: [benchmark]
owner: (none)
priority: P2
severity: bugfix
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: public
source_action_item: (none)
tracker_ref: (none)
execution_backend: any
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-08-15T19:13:56Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:a0782d8f1db48fc33e9122f411e61bf427d21b6d5c647a6402a900ae9bc7c50c
---

# Repair dependency readiness and cycle diagnostics

> **Why:** The medium case tests graph reasoning without allowing a broad write surface.

## Goal

Fix `work/m/task_graph.py` so readiness respects transitive task state and cycle errors name the complete cycle.

## Context

The retained tests cover a diamond dependency graph, one blocked ancestor, and a three-node cycle. Do not change the tests.

## Behavior

- **B-1** — GIVEN a dependency graph WHEN readiness is calculated THEN only pending tasks whose complete dependency set is done are returned in stable order
- **B-2** — GIVEN a cycle WHEN graph validation runs THEN the raised diagnostic names every member and closes the cycle

## Success Criteria

```bash
eval_1() {
  PYTHONDONTWRITEBYTECODE=1 python3 work/m/test_task_graph.py
}
```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "readiness and named-cycle behavior pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
    terminal: true
    expected_duration_sec: 5
retry_policy:
  max_iterations: 8
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [code]
  required_tools: [bash, python3]
  timeout_minutes: 12
  sandbox_type: host
  output_artifacts: [work/m/task_graph.py]
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1
```

## Rollback Plan

Restore only `work/m/task_graph.py`.

## Observability Hooks

(none)

## Anti-Patterns

- Do not special-case the retained fixtures or edit `work/m/test_task_graph.py`.

## Do-Not-Touch

- `work/m/test_task_graph.py`
- `tasks/T-20260815-benchmark-m.md`

## Open Questions

(none)
