---
id: T-20260815-acceptance-finalized-contract
title: "Publish the structured acceptance-finalization contract"
status: done
format_version: 3
profile: full
effort: L
budget_iterations: 12
agent: codex
parent: (none)
depends_on: [T-20260815-release-evidence-contracts]
supersedes: (none)
touches_paths: [CHANGELOG.md, README.md, docs/reference/cli.md, docs/reference/contracts.md, src/dispatch/agent-context.py, tests/schema_contracts.py, tests/test-v36-experience.sh]
creates_paths: [spec/schemas/acceptance-finalized.schema.json, tests/fixtures/acceptance-finalized.json]
source_note: "discovered during the evidence-backed release audit"
created: "2026-08-15T18:22:00Z"
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
signed_off_at: 2026-08-15T18:27:37Z
accepted: true
accepted_by: luanmorenomaciel
accepted_at: 2026-08-15T18:29:33Z
signed_off_sig: hmac-sha256-v3:e2e418a3:e56fc74235db8e20e71b3fba36b31ad3dbe9e9f934893c9417aacc7f783cf7ea
accepted_tier: 1
accepted_attempt_id: 0a5ad087-243a-4ff5-bf20-eb312e7ff8be
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:e56fc74235db8e20e71b3fba36b31ad3dbe9e9f934893c9417aacc7f783cf7ea
acceptance_record_digest: sha256:06fb2cdabcf0814322a628c3368d2578f90a7a9294f42dfeae2a6118b2307c3d
---

# Publish the structured acceptance-finalization contract

> **Why:** JSON-mode acceptance already emits `AcceptanceFinalized/v1`; the public contract needs an explicit schema, fixture, machine context, and documentation.

## Goal

Make the successful acceptance result discoverable and schema-validated without changing its runtime semantics.

## Context

This closes a contract-publication omission found while reviewing the 3.8.1 evidence surface.

## Behavior

- **B-1** — GIVEN a successful JSON-mode acceptance WHEN an external coordinator consumes the result THEN the exact attempt, acceptance-record path, and digest conform to `AcceptanceFinalized/v1`

## Success Criteria

```bash
# eval_1: acceptance finalization contract, docs, and installed context agree
eval_1() {
  python3 tests/schema_contracts.py \
    && bash tests/lint-docs.sh \
    && bash tests/test-v36-experience.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "acceptance finalization contract, docs, and installed context agree"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 120
retry_policy:
  max_iterations: 12
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [schema, fixture, docs, tests]
  required_tools: [git, bash, python3]
  timeout_minutes: 20
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

The schema count and installed `agent-context` contract list expose this addition.

## Anti-Patterns

- Do not imply that a successful JSON envelope grants new authority or replaces `AcceptanceRecord/v1`.

## Do-Not-Touch

- `src/accept/accept-task.sh`
- `bin/taskspec`

## Open Questions

(none — this task is fully specified)
