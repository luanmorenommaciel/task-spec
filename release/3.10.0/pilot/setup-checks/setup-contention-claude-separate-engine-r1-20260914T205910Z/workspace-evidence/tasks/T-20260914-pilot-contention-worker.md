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
touches_paths: []
creates_paths: [tests/fixtures/toolkit/resource-worker.sh]
source_note: "seamwise/legs/LEG-CONTENTION-WORKER.md#T-20260914-pilot-contention-worker"
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
signed_off_at: 2026-09-14T20:59:18Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:2135feb0:3a4eb755d2eb4e51cd26d19ecb5bec08a00d812028f3c1d65198653878039557
---

# Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM

> **Why:** Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

## Goal

Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

## Context

Intent DI-PILOT-CONTENTION; seam SEAM-CONTENTION-WORKER; swimlane LANE-CONTENTION-WORKER; capability leg LEG-CONTENTION-WORKER. Done condition: Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

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
  execution_recipe: {"contract": "TaskExecutionRecipe/v1", "strategy": "diagnose-repair-verify", "strategy_version": "1.0.0", "steps": ["Reproduce the failure and gather evidence before choosing a cause.", "Repair the evidenced cause within scope.", "Verify the reproduction and affected regression checks."], "context": ["TaskHandoff", "authorized Task-Spec", "declared source evidence"], "artifacts": ["scoped changes", "evaluation evidence", "concise result"], "eval_ids": ["eval_1", "eval_2", "eval_3"], "max_rounds": 3, "no_progress_rounds": 2, "stop_on": ["scope_violation", "authority_changed", "environment_unverified", "budget_exhausted", "cancelled"], "on_failure": "park_with_context", "runner": "taskmesh", "required_capabilities": ["managed_recipe_v1", "persistent_round_budget", "signed_timeout"]}
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
