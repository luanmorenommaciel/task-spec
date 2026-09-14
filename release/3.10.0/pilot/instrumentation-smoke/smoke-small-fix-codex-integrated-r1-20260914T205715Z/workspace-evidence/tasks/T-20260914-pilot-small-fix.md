---
id: T-20260914-pilot-small-fix
title: "Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: []
supersedes: (none)
provenance: {"contract": "TaskPlanProvenance/v1", "initiative": "pilot", "projection_digest": "08855d8c557685fe2dc711bf3e7f9594df13e674a30c6eda6456bb50265e8328", "snapshot": "tasks/.plans/pilot/snapshots/a3ddfc92fbf6564f8021f9ee5efa75c5de5dcd32c6973b5ae58440db8138bba4.json", "snapshot_digest": "a3ddfc92fbf6564f8021f9ee5efa75c5de5dcd32c6973b5ae58440db8138bba4"}
proves_capabilities: ["LEG-SMALL-FIX"]
touches_paths: [src/recipe/recipes.py]
creates_paths: []
source_note: "tasks/.plans/pilot/legs/LEG-SMALL-FIX.md#T-20260914-pilot-small-fix"
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
signed_off_by: pilot-controller
signed_off_at: 2026-09-14T20:57:26Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:c3af0a19:7a23864a970b620c502198a28f1669b3b4168b403a2675e999b23d6ab3037017
---

# Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation

> **Why:** Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

## Goal

Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

## Context

Intent DI-PILOT-SMALL-FIX; seam SEAM-SMALL-FIX; swimlane LANE-SMALL-FIX; capability leg LEG-SMALL-FIX. Done condition: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

Applicable intent, capability, and evidence: {"decisions": [{"id": "ADR-PILOT-SCOPE", "owner": "pilot-supervisor", "rationale": "The user authorized real repository issues with prospective intervention recording. This fixed corpus defines the evaluated scope before execution; it does not claim a new human review occurred during each run.", "status": "accepted"}], "evidence": [{"claim": "current", "confidence": 1.0, "id": "E-PILOT-ISSUE", "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "0644414bcd86c5f0db2533901eb442e352d7feaf0cadf526a7e0dc9d392add23", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "summary": "A repository issue inspected before comparative execution; source digests and reproduction are retained."}], "intent": {"claim": "proposed", "id": "DI-PILOT-SMALL-FIX", "out_of_scope": ["Changes outside the registered write surface.", "Production deployment, policy changes, self-authorization, and independent agents."], "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "0644414bcd86c5f0db2533901eb442e352d7feaf0cadf526a7e0dc9d392add23", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "success": ["Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation."], "summary": "Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.", "title": "Valid execution recipes cannot be piped to recipe validate -"}, "lane": {"id": "LANE-SMALL-FIX", "name": "small-fix delivery", "owner": "pilot-small-fix"}, "leg": {"id": "LEG-SMALL-FIX", "observable_state": "Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.", "produces": ["small-fix verified behavior"], "proof": "The declared evaluator succeeds without widening the write surface.", "requires": []}, "original_intake": null, "seam": {"consumes": ["registered issue"], "decision_ids": ["ADR-PILOT-SCOPE"], "description": "Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.", "evidence": ["E-PILOT-ISSUE"], "id": "SEAM-SMALL-FIX", "independent_proof": "Run the registered independent small-fix evaluator.", "name": "small-fix", "owner": "pilot-small-fix", "produces": ["small-fix verified behavior"], "rejected_alternatives": [{"alternative": "Merge this responsibility into an unrelated task", "reason": "Its write surface and independently assessable outcome belong to this boundary."}], "responsibility": "Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation."}}

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for small-fix
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py small-fix --root .
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
    description: "Independent behavioral proof for small-fix"
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
