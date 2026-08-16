---
id: T-20260816-mesh-routes-worktrees
title: "Implement deterministic routing and integration worktrees"
status: done
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260816-mesh-leases-graph]
supersedes: (none)
touches_paths: [internal/mesh/api.go, internal/mesh/daemon.go, internal/mesh/graph.go, internal/mesh/lease.go, internal/mesh/store.go, internal/mesh/types.go, src/mesh/cli.py]
creates_paths: [internal/mesh/integration.go, internal/mesh/routing.go, internal/mesh/worktree.go, tests/test-mesh-routing-integration.sh]
source_note: "user-approved TaskMesh 3.9.0 release plan"
created: "2026-08-16T00:00:00Z"
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
signed_off_at: 2026-08-16T19:57:13Z
accepted: true
accepted_by: luanmorenomaciel
accepted_at: 2026-08-16T19:57:52Z
signed_off_sig: hmac-sha256-v3:e2e418a3:53e9fcf5149e379dc2c415ca015cd2637178a7024c26d5d67ff371c6498381cd
accepted_tier: 1
accepted_attempt_id: 17a92f61-b0e3-4e0d-bca2-c3bd81b60901
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:53e9fcf5149e379dc2c415ca015cd2637178a7024c26d5d67ff371c6498381cd
acceptance_record_digest: sha256:33c9e626163492578723ccce34dcacaa25510ceca84631ae35c832a00d182a5d
---

# Implement deterministic routing and integration worktrees

> **Why:** Executors need deterministic selection and isolated branches while the user's target branch remains untouched.

## Goal

Pin target commits, create run and attempt branches, explain every candidate decision, integrate only accepted conflict-free attempts, and require a human target merge.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN executor capabilities and repository policy WHEN a route is selected THEN every candidate and rejection is recorded and an advisor can only reorder eligible candidates
- **B-2** — GIVEN a run target WHEN attempts execute and integrate THEN TaskMesh owns bounded worktrees and branches while never mutating the target branch
- **B-3** — GIVEN a conflict or target divergence WHEN integration is requested THEN the attempt or run parks with one safe next action and no implicit rebase

## Success Criteria

```bash
# eval_1: route determinism, advisor containment, branch safety, conflicts, and target divergence pass
eval_1() {
  bash tests/test-mesh-routing-integration.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "route determinism, advisor containment, branch safety, conflicts, and target divergence pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3]
    terminal: true
    expected_duration_sec: 180
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

- Do not merge, push, or create a pull request on the user's target branch.

## Do-Not-Touch

- `.github/workflows`

## Open Questions

(none — this task is fully specified)
