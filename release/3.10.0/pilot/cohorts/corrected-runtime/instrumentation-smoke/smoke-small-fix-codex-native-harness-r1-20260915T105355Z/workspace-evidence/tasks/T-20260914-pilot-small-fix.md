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
touches_paths: [src/recipe/recipes.py]
creates_paths: []
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
execution_backend: any
signed_off: true
signed_off_by: pilot-controller
signed_off_at: 2026-09-15T10:54:02Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:5ba326c1:3d5f293f8a5f2ee092e6b3dbf4a5c9419f7706d386017a9ed1a9cf338d9866f0
---

# Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation

> **Why:** Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

## Goal

Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

## Context

Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for small-fix
eval_1() {
  /private/tmp/taskspec-retry-engines/3.10.0/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/pilot/corrected-tooling/task-spec-3.10.0/tests/evals/toolkit/evaluate_issue.py small-fix --root .
}

# eval_2: Declared write surface only
eval_2() {
  /private/tmp/taskspec-retry-engines/3.10.0/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/pilot/corrected-tooling/task-spec-3.10.0/tests/evals/toolkit/evaluate_issue.py write-boundary --root .
}

# eval_3: Registered issue evidence is unchanged
eval_3() {
  /private/tmp/taskspec-retry-engines/3.10.0/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/pilot/corrected-tooling/task-spec-3.10.0/tests/evals/toolkit/evaluate_issue.py source-integrity --root .
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
