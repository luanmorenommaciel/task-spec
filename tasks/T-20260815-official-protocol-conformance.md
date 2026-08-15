---
id: T-20260815-official-protocol-conformance
title: "Correct and externally verify A2A and MCP interop"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260815-release-evidence-contracts]
supersedes: (none)
touches_paths: [src/interop/bridge.py, src/interop/mcp_server.py, spec/schemas/a2a-artifact.schema.json, spec/schemas/mcp-task.schema.json, tests/test-v37-evidence-integrity.sh, release/evidence.json, release/3.8.1/scorecard.json, README.md]
creates_paths: [interop/UPSTREAM.lock, tests/test-protocol-conformance.sh, release/3.8.1/protocol-conformance.json]
source_note: "user-approved release train"
created: "2026-08-15T00:00:00Z"
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
signed_off_at: 2026-08-15T18:38:24Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:508c83ba6b0d5516beb4b93b1773fe3896d6f2fdefb18a2828e35d46208ab5c4
---

# Correct and externally verify A2A and MCP interop

> **Why:** Internal round trips alone cannot support official compatibility claims.

## Goal

Emit A2A v3 and MCP v2 objects, preserve legacy readers, and validate them against pinned official implementations.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN a TaskHandoff v1, v2, or v3 WHEN it is exported and round-tripped through A2A or MCP THEN task revision, authorization, attempt, scope, budgets, and evidence identity are preserved
- **B-2** — GIVEN an unavailable optional SDK WHEN the local core suite runs THEN core compatibility remains testable while release-audit records protocol proof as unavailable

## Success Criteria

```bash
# eval_1: pinned protocol compatibility and legacy parsing tests pass
eval_1() {
  bash tests/test-protocol-conformance.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "pinned protocol compatibility and legacy parsing tests pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
    terminal: true
    expected_duration_sec: 90
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

- Do not claim certification or make experimental MCP Tasks a release dependency.

## Do-Not-Touch

- `src/interop/dsse.py`

## Open Questions

(none — this task is fully specified)
