---
id: T-20260816-mesh-daemon-state
title: "Implement the repository-local TaskMesh daemon and durable state"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260816-mesh-contracts-cli]
supersedes: (none)
touches_paths: [src/mesh/cli.py, .gitignore]
creates_paths: [go.mod, go.sum, cmd/taskspec-meshd/main.go, internal/mesh/api.go, internal/mesh/daemon.go, internal/mesh/repository.go, internal/mesh/store.go, internal/mesh/types.go, tests/test-mesh-daemon.sh]
source_note: "user-approved TaskMesh 3.9.0 release plan"
created: "2026-08-16T00:00:00Z"
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
signed_off_at: 2026-08-16T19:30:47Z
accepted: true
accepted_by: luanmorenomaciel
accepted_at: 2026-08-16T19:38:24Z
signed_off_sig: hmac-sha256-v3:e2e418a3:116f7cbf685d4609b8b35036998bec05dbdd29a716f483069070231578871c6e
accepted_tier: 1
accepted_attempt_id: 412f6f17-ab38-46b5-b2e0-1d1779c73446
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:116f7cbf685d4609b8b35036998bec05dbdd29a716f483069070231578871c6e
acceptance_record_digest: sha256:dc3b310fcdee1f55c93303a0bf77d3c12896fae41eabd87afb2a4a3084f0f157
---

# Implement the repository-local TaskMesh daemon and durable state

> **Why:** Cockpits need one durable repository runtime that survives client exit without moving canonical authority into its database.

## Goal

Build the optional Go helper with SQLite WAL, protected repository-scoped sockets, event replay, idempotent commands, and foreground or auto-start operation.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN one resolved repository WHEN multiple clients connect THEN they negotiate with one daemon identified by the canonical repository path
- **B-2** — GIVEN a daemon restart WHEN durable events are replayed THEN the same TaskMeshView is reconstructed without changing Task-Spec files
- **B-3** — GIVEN runtime directories and sockets WHEN they are created THEN directory and socket permissions are private and runtime state is ignored by Git

## Success Criteria

```bash
# eval_1: daemon lifecycle, SQLite WAL, permissions, idempotency, and replay pass
eval_1() {
  bash tests/test-mesh-daemon.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "daemon lifecycle, SQLite WAL, permissions, idempotency, and replay pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3]
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

- Do not require a hosted service or external database.

## Do-Not-Touch

- `tasks/done`

## Open Questions

(none — this task is fully specified)
