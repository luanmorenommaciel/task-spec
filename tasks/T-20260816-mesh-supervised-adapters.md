---
id: T-20260816-mesh-supervised-adapters
title: "Add native and OMP supervised execution adapters"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260816-mesh-routes-worktrees]
supersedes: (none)
touches_paths: [internal/mesh/api.go, internal/mesh/daemon.go, internal/mesh/store.go, internal/mesh/types.go, src/mesh/cli.py]
creates_paths: [internal/mesh/adapter.go, internal/mesh/process.go, adapters/mesh/codex-native.json, adapters/mesh/claude-native.json, adapters/mesh/grok-native.json, adapters/mesh/omp-rpc.json, tests/fixtures/mesh/fake-adapter.sh, tests/test-mesh-adapters.sh]
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
signed_off: false
signed_off_by: (none)
signed_off_at: (none)
accepted: false
accepted_by: (none)
accepted_at: (none)
---

# Add native and OMP supervised execution adapters

> **Why:** A portable control plane must preserve one atomic handoff and observable attempt across different local harnesses.

## Goal

Probe exact adapter versions, execute one TaskHandoff per attempt, normalize bounded events, enforce timeouts and iteration limits, and support cancellation for Codex, Claude, Grok, and OMP.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN a native or OMP adapter WHEN it probes and executes THEN task revision, scope, budgets, attempt identity, version, events, and receipts survive the boundary
- **B-2** — GIVEN cancellation, timeout, excessive output, or malformed adapter output WHEN TaskMesh handles the process THEN it terminates within bounds, redacts known credentials, and parks with a stable failure code
- **B-3** — GIVEN an OMP attempt WHEN it runs THEN one leaf remains one observable attempt and hidden subagent fan-out is disabled

## Success Criteria

```bash
# eval_1: all adapter contracts pass through a deterministic fake harness and installed probes remain honest
eval_1() {
  bash tests/test-mesh-adapters.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "all adapter contracts pass through a deterministic fake harness and installed probes remain honest"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3]
    terminal: true
    expected_duration_sec: 180
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

- Do not send signing keys, evaluator keys, private holdouts, or broad home-directory access to an adapter.

## Do-Not-Touch

- `adapters/engines`

## Open Questions

(none — this task is fully specified)
