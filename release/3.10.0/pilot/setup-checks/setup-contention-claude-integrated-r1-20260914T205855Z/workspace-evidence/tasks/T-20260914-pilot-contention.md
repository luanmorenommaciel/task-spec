---
id: T-20260914-pilot-contention
title: "Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: [T-20260914-pilot-contention-worker]
supersedes: (none)
provenance: {"contract": "TaskPlanProvenance/v1", "initiative": "pilot", "projection_digest": "8dfeec3825fe6a6f99bfb409f750052128a8140b05245ca667e2e6812388afeb", "snapshot": "tasks/.plans/pilot/snapshots/8070bfc5bbb6c509ccc295dd454751f1e2752a25ce08b37093a5edcfd529fd41.json", "snapshot_digest": "8070bfc5bbb6c509ccc295dd454751f1e2752a25ce08b37093a5edcfd529fd41"}
proves_capabilities: ["LEG-CONTENTION-WORKER", "LEG-CONTENTION"]
touches_paths: []
creates_paths: [tests/test-toolkit-resource-contention.sh]
source_note: "tasks/.plans/pilot/legs/LEG-CONTENTION.md#T-20260914-pilot-contention"
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
signed_off_at: 2026-09-14T20:59:09Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:47daf94b:bf1c75d6ec20ceab0fdb0940f9b7dd16755986cb40f0484257bfe27bfcb99995
---

# Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation

> **Why:** Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.

## Goal

Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.

## Context

Intent DI-PILOT-CONTENTION; seam SEAM-CONTENTION; swimlane LANE-CONTENTION; capability leg LEG-CONTENTION. Done condition: Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.

Applicable intent, capability, and evidence: {"decisions": [{"id": "ADR-PILOT-SCOPE", "owner": "pilot-supervisor", "rationale": "The user authorized real repository issues with prospective intervention recording. This fixed corpus defines the evaluated scope before execution; it does not claim a new human review occurred during each run.", "status": "accepted"}], "evidence": [{"claim": "current", "confidence": 1.0, "id": "E-PILOT-ISSUE", "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "d3a1c617111eeccd8446a31b0a2a86a61674f7b972c8a0e5ab67c06de1a1eac8", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "summary": "A repository issue inspected before comparative execution; source digests and reproduction are retained."}], "intent": {"claim": "proposed", "id": "DI-PILOT-CONTENTION", "out_of_scope": ["Changes outside the registered write surface.", "Production deployment, policy changes, self-authorization, and independent agents."], "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "d3a1c617111eeccd8446a31b0a2a86a61674f7b972c8a0e5ab67c06de1a1eac8", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "success": ["Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state."], "summary": "Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state.", "title": "Shared-resource conflicts across independent runs lack an end-to-end regression scenario"}, "lane": {"id": "LANE-CONTENTION", "name": "contention delivery", "owner": "pilot-contention"}, "leg": {"id": "LEG-CONTENTION", "observable_state": "Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.", "produces": ["contention verified behavior"], "proof": "The declared evaluator succeeds without widening the write surface.", "requires": ["contention-worker verified behavior"]}, "original_intake": null, "seam": {"consumes": ["contention-worker verified behavior"], "decision_ids": ["ADR-PILOT-SCOPE"], "description": "Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.", "evidence": ["E-PILOT-ISSUE"], "id": "SEAM-CONTENTION", "independent_proof": "Run the registered independent contention evaluator.", "name": "contention", "owner": "pilot-contention", "produces": ["contention verified behavior"], "rejected_alternatives": [{"alternative": "Merge this responsibility into an unrelated task", "reason": "Its write surface and independently assessable outcome belong to this boundary."}], "responsibility": "Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout."}}

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for contention
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py contention --root .
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
    description: "Independent behavioral proof for contention"
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
