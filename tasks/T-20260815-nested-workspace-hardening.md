---
id: T-20260815-nested-workspace-hardening
title: "Complete nested-workspace lifecycle hardening"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: []
supersedes: (none)
touches_paths: [src/lib/_lib.sh, src/accept/accept-task.sh, src/accept/preflight.py, src/accept/finalize.py, src/accept/record.py, src/dispatch/handoff.py, tests/test-v38-hardening.sh, tests/test-v36-experience.sh]
creates_paths: [tests/test-v381-workspace.sh]
source_note: "user-approved release train"
created: "2026-08-15T00:00:00Z"
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
execution_backend: codex
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-08-15T17:58:42Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:0cc091ef79095566eb825b033ffdb997552b41ba9f7c7c0b6bd720402cec59bd
---

# Complete nested-workspace lifecycle hardening

> **Why:** Standalone and Converge-style nested workspaces must resolve one safe Git, evaluation, scope, and acceptance boundary.

## Goal

Make workspace-root and acceptance-directory behavior explicit, traversal-safe, symlink-safe, and consistent across the lifecycle.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN a standalone tasks workspace or nested cvg/tasks workspace WHEN handoff, evaluation, blast-radius, and acceptance paths are resolved THEN every lifecycle component uses the same validated repository workspace
- **B-2** — GIVEN an escaped spec, mismatched root, traversal, symlink escape, or conflicting override WHEN the lifecycle is invoked THEN the operation fails closed with no partial acceptance mutation

## Success Criteria

```bash
# eval_1: nested-workspace positive and adversarial cases pass
eval_1() {
  bash tests/test-v381-workspace.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "nested-workspace positive and adversarial cases pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
    terminal: true
    expected_duration_sec: 60
retry_policy:
  max_iterations: 15
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [code, tests]
  required_tools: [git, bash]
  timeout_minutes: 30
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1
```

## Rollback Plan

Revert only the declared write surface and park the task with context.

## Observability Hooks

(none — no runtime observability required)

## Anti-Patterns

- Do not hard-code cvg paths or conflate Converge receipts with Task-Spec acceptance records.

## Do-Not-Touch

- `fixtures/diamond-6`

## Open Questions

(none — this task is fully specified)
