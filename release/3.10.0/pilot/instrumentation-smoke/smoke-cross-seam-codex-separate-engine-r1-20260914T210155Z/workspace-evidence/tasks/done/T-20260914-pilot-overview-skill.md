---
id: T-20260914-pilot-overview-skill
title: "Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state"
status: done
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: [T-20260914-pilot-overview-route]
supersedes: (none)
touches_paths: [SKILL.md, skills/task-spec/SKILL.md]
creates_paths: []
source_note: "seamwise/legs/LEG-OVERVIEW-SKILL.md#T-20260914-pilot-overview-skill"
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
signed_off_at: 2026-09-14T21:02:18Z
accepted: true
accepted_by: luanmorenomaciel
accepted_at: 2026-09-14T21:03:21Z
signed_off_sig: hmac-sha256-v3:607e9815:5df53b4c111a59aa32810a1cebfb464a0d2fcf11b3966c6b187c78f5e80ae7cc
accepted_tier: 1
accepted_attempt_id: 26c4bd3e-fa34-49af-8f1a-278d196ea69e
accepted_authorization_ref: hmac-sha256-v3:607e9815:5df53b4c111a59aa32810a1cebfb464a0d2fcf11b3966c6b187c78f5e80ae7cc
acceptance_record_digest: sha256:d44b0028d7e06caa04b8108a7104a0915e8d7f68244f079eb0198983839a61b8
---

# Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state

> **Why:** Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

## Goal

Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

## Context

Intent DI-PILOT-CROSS-SEAM; seam SEAM-OVERVIEW-SKILL; swimlane LANE-OVERVIEW-SKILL; capability leg LEG-OVERVIEW-SKILL. Done condition: Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for overview-skill
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py cross-seam --root .
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
    description: "Independent behavioral proof for overview-skill"
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
