---
id: T-20260914-chat-output
title: "Complete the output artifact"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: []
supersedes: (none)
provenance: {"contract": "TaskPlanProvenance/v1", "initiative": "managed", "projection_digest": "f6ca2e1c3872483d7455cfc9a0870d2fddfe3b20b786a26f995a11f6ba9b968e", "snapshot": "tasks/.plans/managed/snapshots/d615175149ade1cbe8c897603584e7892de5932badccdecf6e23c47b7f67bde9.json", "snapshot_digest": "d615175149ade1cbe8c897603584e7892de5932badccdecf6e23c47b7f67bde9"}
touches_paths: [a.txt]
creates_paths: []
source_note: "tasks/.plans/managed/legs/LEG-POLICY-SCHEMA-VALID.md#T-20260914-chat-output"
created: "2026-09-14T00:00:00Z"
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
execution_backend: any
signed_off: true
signed_off_by: fixture-controller
signed_off_at: 2026-09-15T10:35:03Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:3452fa61:70a072f848a8f758f135a8558fca43d704862b7d0db67e399be37dd5580bce92
---

# Complete the output artifact

> **Why:** Write the accepted completion value inside one file.

## Goal

Write the accepted completion value inside one file.

## Context

Intent DI-RATE-LIMIT; seam SEAM-POLICY-CONTRACT; swimlane LANE-POLICY-CONTRACT; capability leg LEG-POLICY-SCHEMA-VALID. Done condition: a.txt contains completed and b.txt remains empty.

Applicable intent, capability, and evidence: {"decisions": [{"id": "ADR-RATE-LIMIT-ORDER", "owner": "example-fixture", "rationale": "The fixture follows the blueprint order: schema, effective policy, request 101 enforcement, then visible reason and decision telemetry.", "status": "accepted"}], "evidence": [{"claim": "external", "confidence": 1.0, "id": "E-BLUEPRINT", "source": {"captured_at": "2026-08-02T00:00:00Z", "sha256": "f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445", "uri": "tests/fixtures/toolkit/blueprint.md"}, "summary": "Synthetic blueprint fixture describing the rate-limiting steel thread."}], "intent": {"claim": "proposed", "id": "DI-RATE-LIMIT", "out_of_scope": ["Replacing provider-owned usage metering.", "Choosing production storage or deployment infrastructure."], "source": {"captured_at": "2026-08-02T00:00:00Z", "sha256": "f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445", "uri": "tests/fixtures/toolkit/blueprint.md"}, "success": ["a.txt contains completed and b.txt remains empty"], "summary": "Produce an exact completion artifact while preserving the sibling file.", "title": "Enforce organization-level request limits with visible decisions"}, "lane": {"id": "LANE-POLICY-CONTRACT", "name": "Policy contract lane", "owner": "platform-contracts"}, "leg": {"id": "LEG-POLICY-SCHEMA-VALID", "observable_state": "The completion artifact contains its accepted value", "produces": ["completed artifact"], "proof": "Exact output and untouched sibling checks pass.", "requires": []}, "original_intake": null, "seam": {"consumes": ["authored organization policy"], "decision_ids": ["ADR-RATE-LIMIT-ORDER"], "description": "Separates accepted policy shape from resolution and enforcement.", "evidence": ["E-BLUEPRINT"], "id": "SEAM-POLICY-CONTRACT", "independent_proof": "Read the artifact and independently check its exact bytes.", "name": "Policy contract", "owner": "platform-contracts", "produces": ["completed artifact"], "rejected_alternatives": [{"alternative": "Treat the API handler as the policy boundary", "reason": "Handler ownership would mix contract, resolution, and enforcement concerns."}], "responsibility": "Own the completion artifact"}}

## Behavior

- **B-1** — GIVEN a policy with a positive limit and window WHEN the document is validated THEN schema validation succeeds
- **B-2** — GIVEN a policy with a zero limit or window WHEN the document is validated THEN schema validation fails

## Success Criteria

```bash
# eval_1: The policy schema exists and parses as JSON
eval_1() {
  test "$(cat a.txt)" = completed
}

# eval_2: Valid policy examples pass the schema tests
eval_2() {
  test "$(wc -c < a.txt | tr -d ' ')" = 9
}

# eval_3: Invalid non-positive values are rejected
eval_3() {
  test ! -s b.txt
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "The policy schema exists and parses as JSON"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: false
    expected_duration_sec: 10
  - id: eval_2
    description: "Valid policy examples pass the schema tests"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: false
    expected_duration_sec: 10
  - id: eval_3
    description: "Invalid non-positive values are rejected"
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 10
retry_policy:
  max_iterations: 15
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  execution_recipe: {"artifacts": ["scoped changes", "evaluation evidence", "concise result"], "context": ["TaskHandoff", "authorized Task-Spec", "declared source evidence"], "contract": "TaskExecutionRecipe/v1", "eval_ids": ["eval_1", "eval_2", "eval_3"], "max_rounds": 3, "no_progress_rounds": 2, "on_failure": "park_with_context", "required_capabilities": ["managed_recipe_v1", "persistent_round_budget", "signed_timeout"], "runner": "taskmesh", "steps": ["Reproduce the failure and gather evidence before choosing a cause.", "Repair the evidenced cause within scope.", "Verify the reproduction and affected regression checks."], "stop_on": ["scope_violation", "authority_changed", "environment_unverified", "budget_exhausted", "cancelled"], "strategy": "diagnose-repair-verify", "strategy_version": "1.0.0"}
  read: [intent, behavior, contract, guardrails]
  produce: [code, tests]
  required_tools: [bash]
  timeout_minutes: 30
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1 && eval_2 && eval_3
```

## Rollback Plan

Remove the additive schema and its focused tests.

## Observability Hooks

policy schema test pass count

## Anti-Patterns

- Do not encode limits only in handler constants: downstream resolution would have no versioned contract; instead validate one explicit schema before resolution.
- Do not accept zero or negative windows: enforcement semantics would be undefined; instead reject non-positive values at the contract boundary.
- Do not couple the schema to one storage provider: policy shape and persistence are separate decisions; instead keep the schema provider-neutral.

## Do-Not-Touch

- `tests/fixtures/toolkit/blueprint.md`

## Open Questions

(none — this task is fully specified)
