---
id: T-20260815-real-engine-benchmark
title: "Build and retain the Codex and Claude benchmark matrix"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260815-nested-workspace-hardening, T-20260815-release-evidence-contracts]
supersedes: (none)
touches_paths: [src/evidence/engine_matrix.py, evidence/3.7/engine-matrix.json]
creates_paths: [evidence/3.8.1/engine-matrix.json, evidence/3.8.1/benchmark/README.md, tests/test-engine-matrix-v2.sh, release/3.8.1/engine-matrix-result.json]
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
signed_off_at: 2026-08-15T17:57:19Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:0460435b83f4558c59d9476e3fbfe2c6c73f9a930f510f97caaa33c787b709f5
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
