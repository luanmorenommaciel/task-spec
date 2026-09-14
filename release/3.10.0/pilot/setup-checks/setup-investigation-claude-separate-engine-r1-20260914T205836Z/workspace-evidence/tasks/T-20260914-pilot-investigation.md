---
id: T-20260914-pilot-investigation
title: "Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments, the exact trust boundary, unsupported required environments, and claims not established by Docker smoke evidence"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: []
creates_paths: [docs/maintainers/recipe-assurance-investigation.md]
source_note: "seamwise/legs/LEG-INVESTIGATION.md#T-20260914-pilot-investigation"
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
signed_off_at: 2026-09-14T20:58:45Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:ca097ec3:00480954816b1d0bd5dea2bc3e538fb9ae840dbcb1755faad33f22dd6a3bf656
---

# Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments, the exact trust boundary, unsupported required environments, and claims not established by Docker smoke evidence

> **Why:** Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments, the exact trust boundary, unsupported required environments, and claims not established by Docker smoke evidence. Cite verified source symbols and state remaining uncertainty.

## Goal

Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments, the exact trust boundary, unsupported required environments, and claims not established by Docker smoke evidence. Cite verified source symbols and state remaining uncertainty.

## Context

Intent DI-PILOT-INVESTIGATION; seam SEAM-INVESTIGATION; swimlane LANE-INVESTIGATION; capability leg LEG-INVESTIGATION. Done condition: Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments, the exact trust boundary, unsupported required environments, and claims not established by Docker smoke evidence. Cite verified source symbols and state remaining uncertainty.

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for investigation
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py investigation --root .
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
    description: "Independent behavioral proof for investigation"
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
  execution_recipe: {"contract": "TaskExecutionRecipe/v1", "strategy": "research-synthesize-verify", "strategy_version": "1.0.0", "steps": ["Inspect authoritative sources and record their revisions and evidence limits.", "Synthesize conclusions with source references and explicit uncertainty.", "Verify the claims and requested deliverable against the declared checks."], "context": ["TaskHandoff", "authorized Task-Spec", "declared source evidence"], "artifacts": ["scoped changes", "evaluation evidence", "concise result"], "eval_ids": ["eval_1", "eval_2", "eval_3"], "max_rounds": 3, "no_progress_rounds": 2, "stop_on": ["scope_violation", "authority_changed", "environment_unverified", "budget_exhausted", "cancelled"], "on_failure": "park_with_context", "runner": "taskmesh", "required_capabilities": ["managed_recipe_v1", "persistent_round_budget", "signed_timeout"]}
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
