---
id: T-20260914-release-qualification
title: "Qualify chat behavior and compare three real-work execution workflows"
status: ready
format_version: 3
profile: standard
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260914-release-autonomy]
supersedes: (none)
touches_paths: [tests/evals/toolkit, tests, docs]
creates_paths: [release/3.10.0]
source_note: "User-authorized release goal and prospective repository-issue pilot, 2026-09-14"
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
execution_backend: codex
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-09-14T20:13:03Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:88baf2a50ca935cc477c69d27b9d67aa2743e821d584f353237cb316831232ad
---

# Qualify chat behavior and compare three real-work execution workflows

> **Why:** Complete the full native toolkit release with verifiable evidence and an organized repository.

## Goal

Qualify chat behavior and compare three real-work execution workflows. Preserve established authorization and frozen historical evidence.

## Context

The user explicitly authorized committing and pushing main, creating a release tag and artifact, publishing the release, completing pending capabilities, and running a prospective pilot on real repository issues. Retain historical release evidence and local WATCHDOG.yml bytes.

## Behavior

- **B-1** — GIVEN the approved toolkit and release objective WHEN the scoped release package is completed THEN the package delivers its stated result with direct verification and no unsupported qualification claims

## Success Criteria

```bash
# eval_1: Qualify chat behavior and compare three real-work execution workflows
eval_1() {
  python3 tests/evals/toolkit/pilot.py validate release/3.10.0/pilot/results.json
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Qualify chat behavior and compare three real-work execution workflows"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 900
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

- Do not weaken or edit the eval contract after sign-off.

## Do-Not-Touch

- `WATCHDOG.yml`
- `release/3.9.0`
- `release/3.8.1`
- `release/3.7`

## Open Questions

(none — this task is fully specified)
