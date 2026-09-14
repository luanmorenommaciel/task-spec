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
touches_paths: []
creates_paths: [tests/test-toolkit-resource-contention.sh]
source_note: "tests/fixtures/toolkit/pilot-issue.json"
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
signed_off_at: 2026-09-14T20:59:32Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:d74f75ab:339beaed5387ca25118b30cba3f5c448e093fac13b04f20dc833c28f2a1375f9
---

# Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation

> **Why:** Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state.

## Goal

Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.

## Context

Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.

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
    terminal: true
    expected_duration_sec: 120
  - id: eval_2
    description: "Declared write surface only"
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 120
  - id: eval_3
    description: "Registered issue evidence is unchanged"
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
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

- Do not modify the evaluator or authorize additional work.

## Do-Not-Touch

- `tests/fixtures/toolkit/pilot-issue.json`
- `tasks`

## Open Questions

(none — this task is fully specified)
