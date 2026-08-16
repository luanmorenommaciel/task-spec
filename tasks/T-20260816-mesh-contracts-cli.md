---
id: T-20260816-mesh-contracts-cli
title: "Define TaskMesh contracts and CLI boundary"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: [bin/taskspec, src/dispatch/agent-context.py, spec/schemas/README.md, tests/schema_contracts.py]
creates_paths: [src/mesh/cli.py, spec/schemas/taskmesh-api.schema.json, spec/schemas/taskmesh-run.schema.json, spec/schemas/executor-capability.schema.json, spec/schemas/dispatch-decision.schema.json, spec/schemas/run-lease.schema.json, spec/schemas/taskmesh-event.schema.json, spec/schemas/taskmesh-view.schema.json, spec/schemas/sandbox-evidence.schema.json, spec/schemas/credential-lease.schema.json, tests/test-mesh-contracts.sh]
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
signed_off_at: 2026-08-16T19:25:02Z
accepted: true
accepted_by: luanmorenomaciel
accepted_at: 2026-08-16T19:30:18Z
signed_off_sig: hmac-sha256-v3:e2e418a3:8dc89f86a3f52d59525e3320adb8fa403ed016a76037cd676e50bf9d10e0e88d
accepted_tier: 1
accepted_attempt_id: e4e4fa36-2ca5-42ef-af3d-e54dca45b4fd
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:8dc89f86a3f52d59525e3320adb8fa403ed016a76037cd676e50bf9d10e0e88d
acceptance_record_digest: sha256:4bcdc29c5de4de7c976d5cfe240a1b3cd315d6234e31da9fbc00a2255e7b2187
---

# Define TaskMesh contracts and CLI boundary

> **Why:** The optional control plane needs a typed, version-negotiated boundary before runtime behavior is implemented.

## Goal

Add the complete taskspec mesh namespace, v1alpha1 negotiation, stable typed errors, schemas, and a helper-version handshake without making TaskMesh core authority.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN a core-only installation WHEN a mesh command is requested THEN the CLI explains how to install the optional helper and returns a stable runtime error
- **B-2** — GIVEN TaskMesh contracts and JSON responses WHEN schema and CLI contract tests run THEN every runtime identity, lease, route, event, view, sandbox, and credential object is typed and versioned
- **B-3** — GIVEN a helper whose product version differs from Task-Spec WHEN the CLI negotiates the local API THEN execution fails closed with MESH_VERSION_MISMATCH

## Success Criteria

```bash
# eval_1: TaskMesh schemas, help, JSON, dry-run, and version negotiation pass
eval_1() {
  bash tests/test-mesh-contracts.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "TaskMesh schemas, help, JSON, dry-run, and version negotiation pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3]
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

- Do not let TaskMesh edit Task-Spec frontmatter or become a second authority graph.

## Do-Not-Touch

- `fixtures/diamond-6`

## Open Questions

(none — this task is fully specified)
