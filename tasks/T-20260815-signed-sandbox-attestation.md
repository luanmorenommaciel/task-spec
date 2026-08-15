---
id: T-20260815-signed-sandbox-attestation
title: "Produce externally signed sandbox attestation evidence"
status: in-progress
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260815-release-evidence-contracts, T-20260815-official-protocol-conformance]
supersedes: (none)
touches_paths: [src/evidence/receipts.py, tests/test-v37-evidence-integrity.sh, tests/schema_contracts.py, spec/schemas/environment-attestation.schema.json, release/evidence.json, release/3.8.1, README.md]
creates_paths: [src/evidence/environment_attestation.py, release/docker/Dockerfile, release/docker/run-attestation.sh, tests/test-environment-attestation.sh, release/3.8.1/environment-attestation.json]
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
signed_off_at: 2026-08-15T19:37:22Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:a7b8d3133b7a0bbb369c062189877caba4c24f8f4228a80dd2678592cd4441c4
---

# Produce externally signed sandbox attestation evidence

> **Why:** Environment contracts need external enforcement evidence before portable Tier-1 claims are credible.

## Goal

Attest a locked-down Docker execution, sign the receipt outside the sandbox, and fail closed on mutation.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN Docker and a host-side evaluator key WHEN the reference executor runs in the pinned sandbox THEN the attestation records the actual image, runtime, mounts, limits, command, artifacts, and result
- **B-2** — GIVEN a mutated attestation or receipt WHEN portable acceptance validates it THEN verification fails closed

## Success Criteria

```bash
# eval_1: secret-free attestation fixtures pass and live Docker proof is reported honestly
eval_1() {
  bash tests/test-environment-attestation.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "secret-free attestation fixtures pass and live Docker proof is reported honestly"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
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

- Do not treat an unavailable Docker daemon or self-declared environment as verified enforcement.

## Do-Not-Touch

- `.git/info/taskspec-signing-key`

## Open Questions

(none — this task is fully specified)
