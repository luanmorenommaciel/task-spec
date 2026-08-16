---
id: T-20260816-mesh-autonomous-isolation
title: "Implement autonomous OMP isolation and credential leases"
status: done
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260816-mesh-supervised-adapters]
supersedes: (none)
touches_paths: [internal/mesh/adapter.go, internal/mesh/api.go, internal/mesh/daemon.go, internal/mesh/lease.go, internal/mesh/process.go, internal/mesh/routing.go, internal/mesh/store.go, internal/mesh/types.go, src/mesh/cli.py]
creates_paths: [internal/mesh/credential.go, internal/mesh/sandbox.go, release/mesh/Dockerfile, release/mesh/worker-entrypoint.sh, release/mesh/image.lock, tests/test-mesh-isolation.sh]
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
signed_off_at: 2026-08-16T20:10:58Z
accepted: true
accepted_by: luanmorenomaciel
accepted_at: 2026-08-16T20:30:03Z
signed_off_sig: hmac-sha256-v3:e2e418a3:2db9088d62c78001442d23367ac0b4c8bd4410dd253abd097e0e3d68b36d5e4a
accepted_tier: 1
accepted_attempt_id: 548297a0-4bb5-411f-b674-03bd7a835430
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:2db9088d62c78001442d23367ac0b4c8bd4410dd253abd097e0e3d68b36d5e4a
acceptance_record_digest: sha256:18ae6fcc4d15646ca34d792876fee1025d97fe443988672b96ad01326d7c6922
---

# Implement autonomous OMP isolation and credential leases

> **Why:** Autonomous execution is only credible when workspace, credential, host, and evidence boundaries are externally observable.

## Goal

Add explicit Docker or Podman setup, expiring attempt capabilities, locked-down OMP workers, host-signed sandbox evidence, and fail-closed assurance negotiation.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN verified container and credential boundaries WHEN autonomous OMP execution starts THEN the worker receives only one writable workspace and one expiring provider capability under a fixed route
- **B-2** — GIVEN an unavailable runtime, unverified proxy, missing image digest, or changed sandbox evidence WHEN autonomous mode is requested THEN the attempt fails with a stable code and never silently downgrades
- **B-3** — GIVEN sandbox evidence emitted by the host WHEN canonical acceptance evaluates it THEN it remains bound to the revision, attempt, authorization, base commit, and observed environment

## Success Criteria

```bash
# eval_1: isolation fixtures, credential expiry, no-downgrade rules, and live runtime proof pass
eval_1() {
  bash tests/test-mesh-isolation.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "isolation fixtures, credential expiry, no-downgrade rules, and live runtime proof pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3]
    terminal: true
    expected_duration_sec: 240
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

- Do not mount the host home, Docker socket, SSH agent, signing keys, or evaluator keys into workers.

## Do-Not-Touch

- `release/docker`

## Open Questions

(none — this task is fully specified)
