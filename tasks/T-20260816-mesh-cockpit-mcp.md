---
id: T-20260816-mesh-cockpit-mcp
title: "Deliver the durable cross-harness cockpit and MCP facade"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260816-mesh-autonomous-isolation]
supersedes: (none)
touches_paths: [src/mesh/cli.py, src/interop/mcp_server.py, internal/mesh/api.go, internal/mesh/daemon.go, internal/mesh/integration.go, internal/mesh/lease.go, internal/mesh/process.go, internal/mesh/store.go, internal/mesh/types.go, bin/taskspec, src/dispatch/agent-context.py]
creates_paths: [src/mesh/mcp_server.py, tests/test-mesh-cockpit.sh]
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

# Deliver the durable cross-harness cockpit and MCP facade

> **Why:** Codex, Claude, or Grok should be able to act as a reconnectable cockpit without owning the durable runtime.

## Goal

Expose frontier, routing, start, observe, cancel, supervised accept, resume, and finish over CLI and local MCP while preserving canonical acceptance authority.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN a durable run WHEN one cockpit closes and another connects THEN the second cockpit observes the same ordered history and authorized controls
- **B-2** — GIVEN MCP tools or CLI mutations WHEN they act on a run THEN they negotiate TaskMeshAPI, share typed results, honor dry-run, and cannot bypass leases or Task-Spec acceptance
- **B-3** — GIVEN a finished integration branch WHEN finish runs THEN it prints the human merge route without mutating the target branch

## Success Criteria

```bash
# eval_1: cross-cockpit reconnection, MCP round trips, authorization, and human finish pass
eval_1() {
  bash tests/test-mesh-cockpit.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "cross-cockpit reconnection, MCP round trips, authorization, and human finish pass"
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

- Do not depend on the experimental MCP Tasks extension or a specific cockpit vendor.

## Do-Not-Touch

- `interop/UPSTREAM.lock`

## Open Questions

(none — this task is fully specified)
