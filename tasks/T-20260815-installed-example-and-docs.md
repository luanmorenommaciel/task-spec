---
id: T-20260815-installed-example-and-docs
title: "Deliver the installed example and reviewer-grade documentation"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260815-quality-release-audit, T-20260815-official-protocol-conformance]
supersedes: (none)
touches_paths: [bin/taskspec, src/dispatch/agent-context.py, README.md, docs/reference/cli.md, tests/readme_contract.py]
creates_paths: [src/author/examples.py, docs/getting-started/reviewer-route.md, tests/test-v381-experience.sh]
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
signed_off_at: 2026-08-15T17:57:10Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:b7dd7f20a1182f97e95728af347ff3e395b317957167b957a793d6957bbe27c5
---

# Deliver the installed example and reviewer-grade documentation

> **Why:** Reviewers need a source-checkout-independent path whose commands and claims execute exactly as documented.

## Goal

Add taskspec example task-plan and a five-minute evidence-review journey with generated status.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN a globally installed Task-Spec release WHEN taskspec example task-plan is invoked THEN the canonical example is written non-clobberingly with JSON and dry-run parity
- **B-2** — GIVEN the README and reviewer route WHEN documentation tests execute them in a clean repository THEN commands, links, fences, help, envelopes, and claims agree with retained evidence

## Success Criteria

```bash
# eval_1: installed example and reviewer journey pass
eval_1() {
  bash tests/test-v381-experience.sh && bash tests/test-readme-contract.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "installed example and reviewer journey pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
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

- Do not require a source checkout or hand-maintain the public quality total.

## Do-Not-Touch

- `assets/readme`

## Open Questions

(none — this task is fully specified)
