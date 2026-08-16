---
id: T-20260816-mesh-leases-graph
title: "Connect the authorized graph to leases, fencing, and recovery"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260816-mesh-daemon-state]
supersedes: (none)
touches_paths: [internal/mesh/api.go, internal/mesh/daemon.go, internal/mesh/store.go, internal/mesh/types.go, src/mesh/cli.py]
creates_paths: [internal/mesh/graph.go, internal/mesh/lease.go, internal/mesh/recovery.go, tests/test-mesh-leases.sh]
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

# Connect the authorized graph to leases, fencing, and recovery

> **Why:** Only authorized ready leaves may be scheduled, and stale workers must never regain authority after recovery.

## Goal

Resolve TaskGraphView, build write-disjoint waves, issue monotonically fenced leases, heartbeat them, cancel them, and recover deterministically.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN a derived graph with blocked, unsigned, node, and conflicting tasks WHEN TaskMesh computes the frontier THEN only Tier-1 authorized ready leaves enter a write-disjoint wave
- **B-2** — GIVEN simultaneous lease requests WHEN they target one task revision THEN exactly one fencing token remains authoritative
- **B-3** — GIVEN an expired lease, daemon crash, duplicate result, or late worker WHEN processing resumes THEN stale results fail closed and a new fenced attempt can recover safely

## Success Criteria

```bash
# eval_1: graph eligibility, concurrency, fencing, crash recovery, and idempotency pass
eval_1() {
  bash tests/test-mesh-leases.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "graph eligibility, concurrency, fencing, crash recovery, and idempotency pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3]
    terminal: true
    expected_duration_sec: 150
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

- Do not create dependencies at runtime or treat write conflicts as authorization.

## Do-Not-Touch

- `src/graph/task_graph.py`

## Open Questions

(none — this task is fully specified)
