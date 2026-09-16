---
id: T-20260914-toolkit-sdlc
title: "Validate operational evidence and expose read-only initiative inspection"
status: done
format_version: 3
profile: standard
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260914-toolkit-mesh]
supersedes: (none)
touches_paths: [src/interop, src/evidence, docs/examples]
creates_paths: [tests/test-toolkit-sdlc.sh]
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
signed_off_at: 2026-09-14T16:52:51Z
accepted: true
accepted_by: codex-release-supervisor
accepted_at: 2026-09-16T02:39:22Z
signed_off_sig: hmac-sha256-v3:e2e418a3:cd2de4ce89b0f2f0ac4cc94fac594621bc294da61c4067d749ea546a36b2689d
accepted_tier: 1
accepted_attempt_id: be848bba-c137-4951-88f6-db16cce0d720
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:cd2de4ce89b0f2f0ac4cc94fac594621bc294da61c4067d749ea546a36b2689d
acceptance_record_digest: sha256:9872387720ad0e6e6ee79db516d37bb919fa8f5921b380322a2789afaf3a4c5a
---

# Validate operational evidence and expose read-only initiative inspection

> **Why:** Deliver the explicitly approved native TaskSpec toolkit while preserving authorization and acceptance.

## Goal

Validate operational evidence and expose read-only initiative inspection. Preserve established interfaces and prove the requested behavior with the named regression check.

## Context

Implementation is explicitly authorized by the user. Leave Git history unchanged. Historical release and accepted-task evidence and WATCHDOG.yml are outside scope.

## Behavior

- **B-1** — GIVEN the current TaskSpec checkout and approved toolkit design WHEN the bounded package is implemented THEN the package check demonstrates its behavior and compatibility

## Success Criteria

```bash
# eval_1: Validate operational evidence and expose read-only initiative inspection
eval_1() {
  bash tests/test-toolkit-sdlc.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Validate operational evidence and expose read-only initiative inspection"
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
