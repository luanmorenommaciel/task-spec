---
id: T-20260914-pilot-incident
title: "Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: []
supersedes: (none)
provenance: {"contract": "TaskPlanProvenance/v1", "initiative": "pilot", "projection_digest": "b88ae5388010643b5c2b0232b2b91b8f1048d959705ba94e1cb9af77cb20bf53", "snapshot": "tasks/.plans/pilot/snapshots/603f7a41fc97a5825678d2c6185a47f79ec17949b4eaa25aa0d467f1b758d61a.json", "snapshot_digest": "603f7a41fc97a5825678d2c6185a47f79ec17949b4eaa25aa0d467f1b758d61a"}
proves_capabilities: ["LEG-INCIDENT"]
touches_paths: [src/evidence/operational.py]
creates_paths: []
source_note: "tasks/.plans/pilot/legs/LEG-INCIDENT.md#T-20260914-pilot-incident"
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
execution_backend: claude
signed_off: true
signed_off_by: pilot-controller
signed_off_at: 2026-09-14T20:59:55Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:c02b9f92:3c1c6317ed64d85b59ec0f7302f67d925a8f706240e9deecebdfa0123c099368
---

# Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID

> **Why:** Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and prohibit health or acceptance promotion.

## Goal

Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and prohibit health or acceptance promotion.

## Context

Intent DI-PILOT-INCIDENT; seam SEAM-INCIDENT; swimlane LANE-INCIDENT; capability leg LEG-INCIDENT. Done condition: Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and prohibit health or acceptance promotion.

Applicable intent, capability, and evidence: {"decisions": [{"id": "ADR-PILOT-SCOPE", "owner": "pilot-supervisor", "rationale": "The user authorized real repository issues with prospective intervention recording. This fixed corpus defines the evaluated scope before execution; it does not claim a new human review occurred during each run.", "status": "accepted"}], "evidence": [{"claim": "current", "confidence": 1.0, "id": "E-PILOT-ISSUE", "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "c0183f60ddf3d93d84864cc710e3afd3447caead3920173f91a27a95ce59c610", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "summary": "A repository issue inspected before comparative execution; source digests and reproduction are retained."}], "intent": {"claim": "proposed", "id": "DI-PILOT-INCIDENT", "out_of_scope": ["Changes outside the registered write surface.", "Production deployment, policy changes, self-authorization, and independent agents."], "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "c0183f60ddf3d93d84864cc710e3afd3447caead3920173f91a27a95ce59c610", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "success": ["Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and prohibit health or acceptance promotion."], "summary": "Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and prohibit health or acceptance promotion.", "title": "A malformed imported incident receipt raises a raw TypeError"}, "lane": {"id": "LANE-INCIDENT", "name": "incident delivery", "owner": "pilot-incident"}, "leg": {"id": "LEG-INCIDENT", "observable_state": "Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and prohibit health or acceptance promotion.", "produces": ["incident verified behavior"], "proof": "The declared evaluator succeeds without widening the write surface.", "requires": []}, "original_intake": null, "seam": {"consumes": ["registered issue"], "decision_ids": ["ADR-PILOT-SCOPE"], "description": "Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and prohibit health or acceptance promotion.", "evidence": ["E-PILOT-ISSUE"], "id": "SEAM-INCIDENT", "independent_proof": "Run the registered independent incident evaluator.", "name": "incident", "owner": "pilot-incident", "produces": ["incident verified behavior"], "rejected_alternatives": [{"alternative": "Merge this responsibility into an unrelated task", "reason": "Its write surface and independently assessable outcome belong to this boundary."}], "responsibility": "Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and prohibit health or acceptance promotion."}}

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for incident
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py incident --root .
}

# eval_2: Declared write surface only
eval_2() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py write-boundary --root .
}

# eval_3: Registered issue evidence is unchanged
eval_3() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py source-integrity --root .
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Independent behavioral proof for incident"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: false
    expected_duration_sec: 10
  - id: eval_2
    description: "Declared write surface only"
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: false
    expected_duration_sec: 10
  - id: eval_3
    description: "Registered issue evidence is unchanged"
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
  required_tools: [git, bash, python3]
  timeout_minutes: 10
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

Revert only this isolated candidate change.

## Observability Hooks

Retained provider output, evaluation result, and prospective event journal.

## Anti-Patterns

- Do not weaken the independent evaluator: it would invalidate the comparison; instead fix the behavior within the declared surface.
- Do not expand the scope: it breaks matched permissions; instead report the missing work as a blocker.
- Do not claim success without evidence: a plausible patch does not establish behavior; instead run the independent proof and report failures.

## Do-Not-Touch

- `tests/fixtures/toolkit/pilot-issue.json`
- `tasks`

## Open Questions

(none — this task is fully specified)
