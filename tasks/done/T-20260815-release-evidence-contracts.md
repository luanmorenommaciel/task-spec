---
id: T-20260815-release-evidence-contracts
title: "Add versioned 3.8.1 release-evidence contracts"
status: done
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260815-nested-workspace-hardening]
supersedes: (none)
touches_paths: [spec/schemas/README.md, tests/schema_contracts.py, docs/reference/contracts.md]
creates_paths: [spec/schemas/quality-rubric.schema.json, spec/schemas/task-spec-quality-scorecard.schema.json, spec/schemas/task-spec-release-evidence.schema.json, spec/schemas/engine-matrix.schema.json, spec/schemas/engine-matrix-result.schema.json, spec/schemas/protocol-conformance-evidence.schema.json, spec/schemas/environment-attestation.schema.json, tests/test-release-evidence-contracts.sh]
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
signed_off_at: 2026-08-15T18:07:14Z
accepted: true
accepted_by: luanmorenomaciel
accepted_at: 2026-08-15T18:09:45Z
signed_off_sig: hmac-sha256-v3:e2e418a3:92cf20bf14f4e1c63cf3400c3ad2b9d3f0dac3b780dcb7bf4d41831cf5796abf
accepted_tier: 1
accepted_attempt_id: e3c2d208-284e-43ff-866c-d85a819cb30a
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:92cf20bf14f4e1c63cf3400c3ad2b9d3f0dac3b780dcb7bf4d41831cf5796abf
acceptance_record_digest: sha256:eed94c0611421b6c04a4ab96a49973febf4888ccc387632943b00dea26faa201
---

# Add versioned 3.8.1 release-evidence contracts

> **Why:** Quality and release claims need typed, independently validatable evidence rather than prose.

## Goal

Define and validate the complete evidence contract set required by the 3.8.1 release audit.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN a release rubric, scorecard, engine result, protocol result, or environment attestation WHEN schema validation runs THEN valid typed evidence passes and malformed or incomplete evidence fails

## Success Criteria

```bash
# eval_1: all evidence schemas and fixtures satisfy the schema contract suite
eval_1() {
  bash tests/test-release-evidence-contracts.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "all evidence schemas and fixtures satisfy the schema contract suite"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 30
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

- Do not encode a claimed score without artifact references and digests.

## Do-Not-Touch

- `spec/task-spec-v3.md`
- `spec/task-spec-v4.md`

## Open Questions

(none — this task is fully specified)
