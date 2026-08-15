---
id: T-20260815-benchmark-xs
title: "Create the exact atomic marker"
status: ready
format_version: 3
profile: standard
effort: XS
budget_iterations: 3
agent: any
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: []
creates_paths: [work/xs/result.txt]
source_note: "Task-Spec 3.8.1 frozen engine benchmark"
created: "2026-08-15T00:00:00Z"
tags: [benchmark]
owner: (none)
priority: P2
severity: feature
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: public
source_action_item: (none)
tracker_ref: (none)
execution_backend: any
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-08-15T19:06:41Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:0db911a2bac7820fb58b4312fbc7f5d557e5b6fdc92e279f66b7cbf037bb36c9
---

# Create the exact atomic marker

> **Why:** The smallest benchmark proves that an executor can honor one exact write and value.

## Goal

Create `work/xs/result.txt` containing exactly `task-spec-xs-ok` followed by one newline.

## Context

The file does not exist. Do not modify the Task-Spec.

## Behavior

- **B-1** — GIVEN an empty XS workspace WHEN the task executes THEN `work/xs/result.txt` contains exactly the authorized marker

## Success Criteria

```bash
eval_1() {
  test "$(cat work/xs/result.txt)" = "task-spec-xs-ok"
}
```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "the exact XS marker exists"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 1
retry_policy:
  max_iterations: 3
  circuit_breaker_no_progress: 2
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [code]
  required_tools: [bash]
  timeout_minutes: 5
  sandbox_type: host
  output_artifacts: [work/xs/result.txt]
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1
```

## Rollback Plan

Delete only `work/xs/result.txt`.

## Observability Hooks

(none)

## Anti-Patterns

- Do not edit the task or create another file.

## Do-Not-Touch

- `tasks/T-20260815-benchmark-xs.md`

## Open Questions

(none)
