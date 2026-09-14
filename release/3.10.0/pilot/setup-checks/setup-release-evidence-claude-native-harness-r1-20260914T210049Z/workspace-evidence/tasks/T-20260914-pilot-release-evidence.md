---
id: T-20260914-pilot-release-evidence
title: "Exclude WATCHDOG"
status: ready
format_version: 3
profile: standard
effort: M
budget_iterations: 15
agent: any
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: [tools/build-release-archive.py]
creates_paths: [docs/examples/pilot-release-evidence.json, docs/examples/pilot-artifacts]
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
signed_off_at: 2026-09-14T21:00:56Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:8fdcd99e:808f8ec58703be20d6fa2117ed583ff0ab28ab9d46ebefdbdf41b292040b906f
---

# Exclude WATCHDOG

> **Why:** Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.

## Goal

Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.

## Context

Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for release-evidence
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py release-evidence --root .
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
    description: "Independent behavioral proof for release-evidence"
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
