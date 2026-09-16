---
id: T-20260914-toolkit-runtime
title: "Validate signed managed recipe limits and forbid unsafe execution modes"
status: done
format_version: 3
profile: standard
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260914-toolkit-packaging]
supersedes: (none)
touches_paths: [src/gate/validate-runtime.py]
creates_paths: [tests/test-toolkit-runtime.sh]
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
signed_off_at: 2026-09-14T16:52:48Z
accepted: true
accepted_by: codex-release-supervisor
accepted_at: 2026-09-16T02:42:21Z
signed_off_sig: hmac-sha256-v3:e2e418a3:58e6fef8e3b31a0607ab5084f80df8a838bd6186c497e26b1d0a83f09dc899b0
accepted_tier: 1
accepted_attempt_id: c0c86667-e335-437a-8158-f6d3b3c18e1f
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:58e6fef8e3b31a0607ab5084f80df8a838bd6186c497e26b1d0a83f09dc899b0
acceptance_record_digest: sha256:13ef537e73cedb342cb8474cd3e910e570cb15ba68b0e786de4938bfd137626c
---

# Validate signed managed recipe limits and forbid unsafe execution modes

> **Why:** Deliver the explicitly approved native TaskSpec toolkit while preserving authorization and acceptance.

## Goal

Validate signed managed recipe limits and forbid unsafe execution modes. Preserve current task semantics and verify with the package check.

## Context

Implementation is explicitly authorized by the user. Leave Git history unchanged. Historical release and accepted-task evidence and WATCHDOG.yml are outside scope.

## Behavior

- **B-1** — GIVEN the current TaskSpec checkout and approved toolkit design WHEN the bounded package is implemented THEN the package check demonstrates its behavior and compatibility

## Success Criteria

```bash
# eval_1: Validate signed managed recipe limits and forbid unsafe execution modes
eval_1() {
  bash tests/test-toolkit-runtime.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Validate signed managed recipe limits and forbid unsafe execution modes"
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
