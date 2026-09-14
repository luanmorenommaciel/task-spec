---
id: T-20260914-toolkit-mesh
title: "Enforce bounded recipe rounds and persistent graph execution budgets"
status: ready
format_version: 3
profile: standard
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260914-toolkit-authoring]
supersedes: (none)
touches_paths: [mesh/internal/mesh, src/meshctl, src/graph]
creates_paths: [tests/test-toolkit-mesh.sh]
source_note: "User-approved integrated toolkit implementation plan, 2026-09-14"
created: "2026-09-14T00:00:00Z"
tags: []
owner: (none)
priority: P2
severity: feature
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: (none)
source_action_item: (none)
tracker_ref: (none)
execution_backend: codex
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-09-14T17:02:54Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:d12b144f4673c831dd1bf4bdce4a840b3f03b58605be99a2eea96b2dc1ebc4aa
---

# Enforce bounded recipe rounds and persistent graph execution budgets

> **Why:** Deliver the explicitly approved native TaskSpec toolkit while preserving authorization and acceptance.

## Goal

Enforce bounded recipe rounds and persistent graph execution budgets. Preserve established interfaces and prove the requested behavior with the named regression check.

## Context

Implementation is explicitly authorized by the user. Leave Git history unchanged. Historical release and accepted-task evidence and WATCHDOG.yml are outside scope.

## Behavior

- **B-1** — GIVEN the current TaskSpec checkout and approved toolkit design WHEN the bounded package is implemented THEN the package check demonstrates its behavior and compatibility

## Success Criteria

```bash
# eval_1: Enforce bounded recipe rounds and persistent graph execution budgets
eval_1() {
  bash tests/test-toolkit-mesh.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Enforce bounded recipe rounds and persistent graph execution budgets"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 120
retry_policy:
  max_iterations: 15
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [code, tests]
  required_tools: [git, bash]
  timeout_minutes: 30
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1
```

## Rollback Plan

Revert only the declared write surface and park the task with context.

## Observability Hooks

(none — no runtime observability required)

## Anti-Patterns

- Do not weaken or edit the eval contract after sign-off.

## Do-Not-Touch

- `WATCHDOG.yml`
- `release/3.9.0`
- `tasks/done`
- `.taskspec/acceptance`

## Open Questions

(none — this task is fully specified)
