---
id: T-20260815-real-engine-benchmark
title: "Build and retain the Codex and Claude benchmark matrix"
status: done
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260815-nested-workspace-hardening, T-20260815-release-evidence-contracts]
supersedes: (none)
touches_paths: [src/evidence/engine_matrix.py, evidence/3.7/engine-matrix.json, release/evidence.json, release/3.8.1, README.md]
creates_paths: [evidence/3.8.1, tests/test-engine-matrix-v2.sh]
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
signed_off_at: 2026-08-15T19:04:31Z
accepted: true
accepted_by: luanmorenomaciel
accepted_at: 2026-08-15T19:30:17Z
signed_off_sig: hmac-sha256-v3:e2e418a3:fe5d1459277a96f408d0e4c6a78e09b820d3d00ac04c34558724b1619095e23f
accepted_tier: 1
accepted_attempt_id: 7fb19d36-7a0b-4bdf-9e55-fbd797be0a81
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:fe5d1459277a96f408d0e4c6a78e09b820d3d00ac04c34558724b1619095e23f
acceptance_record_digest: sha256:b555f0d350ff8a3ca562b6a25f406aef9b575f89dd476a6e473d02e42bd3f8dc
---

# Build and retain the Codex and Claude benchmark matrix

> **Why:** Portable handoff claims need retained evidence from more than the bundled reference executor.

## Goal

Freeze XS, S, and M tasks and run one guarded attempt through Codex and Claude with honest result retention.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN the frozen three-task benchmark WHEN an enabled engine family runs it THEN every attempt retains identity, command, version, patch, scope, timing, usage, transcript digest, and acceptance result
- **B-2** — GIVEN a disabled, failed, or unavailable engine WHEN results are summarized THEN the state remains visible and cannot be counted as a pass

## Success Criteria

```bash
# eval_1: engine matrix v2 fixtures and honest availability rules pass
eval_1() {
  bash tests/test-engine-matrix-v2.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "engine matrix v2 fixtures and honest availability rules pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
    terminal: true
    expected_duration_sec: 60
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

- Do not remove failures, retry selectively, or expose signing keys and private evaluator instructions.

## Do-Not-Touch

- `evidence/3.7`

## Open Questions

(none — this task is fully specified)
