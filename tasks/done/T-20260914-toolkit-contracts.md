---
id: T-20260914-toolkit-contracts
title: "Define native toolkit contracts and preserve existing task formats"
status: done
format_version: 3
profile: standard
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: [OPERATING.md, AGENTS.md, CHANGELOG.md, spec/schemas, spec/conformance]
creates_paths: []
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
signed_off_at: 2026-09-14T16:52:35Z
accepted: true
accepted_by: codex-release-supervisor
accepted_at: 2026-09-16T02:36:27Z
signed_off_sig: hmac-sha256-v3:e2e418a3:5556ee2cf95926a81557f38c6b0485eea00a0083897a0cc31edcd5e040f84454
accepted_tier: 1
accepted_attempt_id: 213d5dd4-30c4-4763-83bc-5af7f9f1019f
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:5556ee2cf95926a81557f38c6b0485eea00a0083897a0cc31edcd5e040f84454
acceptance_record_digest: sha256:f0446a8d6e199b80dd64813a4ea20aa5d635a04f9f12bb3cc62d07576fd033d2
---

# Define native toolkit contracts and preserve existing task formats

> **Why:** Deliver the explicitly approved native TaskSpec toolkit while preserving authorization and acceptance.

## Goal

Define native toolkit contracts and preserve existing task formats. Preserve established interfaces and prove the requested behavior with the named regression check.

## Context

Implementation is explicitly authorized by the user. Leave Git history unchanged. Historical release and accepted-task evidence and WATCHDOG.yml are outside scope.

## Behavior

- **B-1** — GIVEN the current TaskSpec checkout and approved toolkit design WHEN the bounded package is implemented THEN the package check demonstrates its behavior and compatibility

## Success Criteria

```bash
# eval_1: Define native toolkit contracts and preserve existing task formats
eval_1() {
  bash spec/conformance/run_conformance.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Define native toolkit contracts and preserve existing task formats"
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
