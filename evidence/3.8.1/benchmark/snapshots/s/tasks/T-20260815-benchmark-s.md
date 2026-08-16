---
id: T-20260815-benchmark-s
title: "Repair deterministic search CLI output"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 5
agent: any
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: [work/s/search_cli.py]
creates_paths: []
source_note: "Task-Spec 3.8.1 frozen engine benchmark"
created: "2026-08-15T00:00:00Z"
tags: [benchmark]
owner: (none)
priority: P2
severity: bugfix
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: public
source_action_item: (none)
tracker_ref: (none)
execution_backend: any
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-08-15T19:06:43Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:7c51ffaea58f5786bd21d0f069273e9043fe700af37bfd777004e3612d6a4e61
---

# Repair deterministic search CLI output

> **Why:** A small CLI tests behavior across both human and machine-readable surfaces.

## Goal

Fix `work/s/search_cli.py` so the retained tests pass without changing the tests.

## Context

The CLI has two defects: JSON output is not valid JSON and the no-result human message is incorrect.

## Behavior

- **B-1** — GIVEN query `task` and `--json` WHEN the CLI runs THEN it emits the exact structured result required by the tests
- **B-2** — GIVEN a query with no matches WHEN human output runs THEN it prints `No results for: <query>`

## Success Criteria

```bash
eval_1() {
  python3 work/s/test_search_cli.py
}
```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "human and JSON search output agree with the contract"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
    terminal: true
    expected_duration_sec: 3
retry_policy:
  max_iterations: 5
  circuit_breaker_no_progress: 2
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [code]
  required_tools: [bash, python3]
  timeout_minutes: 8
  sandbox_type: host
  output_artifacts: [work/s/search_cli.py]
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1
```

## Rollback Plan

Restore only `work/s/search_cli.py`.

## Observability Hooks

(none)

## Anti-Patterns

- Do not weaken or modify `work/s/test_search_cli.py`.

## Do-Not-Touch

- `work/s/test_search_cli.py`
- `tasks/T-20260815-benchmark-s.md`

## Open Questions

(none)
