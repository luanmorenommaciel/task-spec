---
id: T-20260914-pilot-contention-worker
title: "Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: []
supersedes: (none)
provenance: {"contract": "TaskPlanProvenance/v1", "initiative": "pilot", "projection_digest": "91fb5f88e8321b0521fe3f01c63a1e77aecd3202d5db059be9271de7a101b9ae", "snapshot": "tasks/.plans/pilot/snapshots/8070bfc5bbb6c509ccc295dd454751f1e2752a25ce08b37093a5edcfd529fd41.json", "snapshot_digest": "8070bfc5bbb6c509ccc295dd454751f1e2752a25ce08b37093a5edcfd529fd41"}
touches_paths: []
creates_paths: [tests/fixtures/toolkit/resource-worker.sh]
source_note: "tasks/.plans/pilot/legs/LEG-CONTENTION-WORKER.md#T-20260914-pilot-contention-worker"
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
signed_off_at: 2026-09-14T20:59:06Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:47daf94b:0148e5f56b62c59095e7c61c25e45ce8b51e6d76c42ba66d1a0acb52aaf6bafe
---

# Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM

> **Why:** Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

## Goal

Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

## Context

Intent DI-PILOT-CONTENTION; seam SEAM-CONTENTION-WORKER; swimlane LANE-CONTENTION-WORKER; capability leg LEG-CONTENTION-WORKER. Done condition: Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

Applicable intent, capability, and evidence: {"decisions": [{"id": "ADR-PILOT-SCOPE", "owner": "pilot-supervisor", "rationale": "The user authorized real repository issues with prospective intervention recording. This fixed corpus defines the evaluated scope before execution; it does not claim a new human review occurred during each run.", "status": "accepted"}], "evidence": [{"claim": "current", "confidence": 1.0, "id": "E-PILOT-ISSUE", "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "d3a1c617111eeccd8446a31b0a2a86a61674f7b972c8a0e5ab67c06de1a1eac8", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "summary": "A repository issue inspected before comparative execution; source digests and reproduction are retained."}], "intent": {"claim": "proposed", "id": "DI-PILOT-CONTENTION", "out_of_scope": ["Changes outside the registered write surface.", "Production deployment, policy changes, self-authorization, and independent agents."], "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "d3a1c617111eeccd8446a31b0a2a86a61674f7b972c8a0e5ab67c06de1a1eac8", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "success": ["Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state."], "summary": "Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state.", "title": "Shared-resource conflicts across independent runs lack an end-to-end regression scenario"}, "lane": {"id": "LANE-CONTENTION-WORKER", "name": "contention-worker delivery", "owner": "pilot-contention-worker"}, "leg": {"id": "LEG-CONTENTION-WORKER", "observable_state": "Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.", "produces": ["contention-worker verified behavior"], "proof": "The declared evaluator succeeds without widening the write surface.", "requires": []}, "original_intake": null, "seam": {"consumes": ["registered issue"], "decision_ids": ["ADR-PILOT-SCOPE"], "description": "Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.", "evidence": ["E-PILOT-ISSUE"], "id": "SEAM-CONTENTION-WORKER", "independent_proof": "Run the registered independent contention-worker evaluator.", "name": "contention-worker", "owner": "pilot-contention-worker", "produces": ["contention-worker verified behavior"], "rejected_alternatives": [{"alternative": "Merge this responsibility into an unrelated task", "reason": "Its write surface and independently assessable outcome belong to this boundary."}], "responsibility": "Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers."}}

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for contention-worker
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py contention-worker --root .
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
    description: "Independent behavioral proof for contention-worker"
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
