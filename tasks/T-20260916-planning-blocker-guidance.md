---
id: T-20260916-planning-blocker-guidance
title: "Explain planning blockers without implying completed validation"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 3
agent: codex
parent: (none)
depends_on: [T-20260914-toolkit-experience]
supersedes: (none)
touches_paths: [SKILL.md, skills/task-spec/SKILL.md, src/decompose/cli.py, tests/test-toolkit-decompose.sh]
creates_paths: []
source_note: "User-authorized full release completion and retained Claude planning denial, 2026-09-15"
created: "2026-09-16T13:45:46Z"
tags: []
owner: (none)
priority: P2
severity: bugfix
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: (none)
source_action_item: (none)
tracker_ref: (none)
execution_backend: codex
signed_off: true
signed_off_by: codex-supervisor-under-user-authority
signed_off_at: 2026-09-16T13:47:22Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:c65688c197ab22f5971a63e57a6a146335235cfb3b1e1cf80d02b5248ba055f2
---

# Explain planning blockers without implying completed validation

> **Why:** The retained planning observation treated a decision blocker as a validation repair target and claimed later checks passed. The CLI recovery instruction was generic.

## Goal

Preserve diagnostic codes internally so preparation errors caused by missing ownership, unaccepted decisions, or unresolved architecture request the missing human input. Keep malformed-input repair actionable. Clarify that blocked validation leaves later checks unproven and that throwaway probes must not manufacture decisions. Maintain root and packaged skill parity.

## Context

The user authorized full release completion. Evidence is release/3.10.0/qualification/workspace-path-retry/chat/runs/plan-claude-20260916T133941Z/behavior-review.json. This correction does not authorize another provider observation, widen permissions, alter diagnostic codes or exit codes, or weaken original release criteria.

## Behavior

- **B-1** — GIVEN a missing decision, owner, or architecture input WHEN prepare fails THEN recovery requests the missing input and preserves unresolved state rather than instructing an unconditional retry
- **B-2** — GIVEN a malformed recipe WHEN prepare fails THEN ordinary correction guidance remains available, existing exit codes persist, and dry-run does not mutate the workspace
- **B-3** — GIVEN blocked validation WHEN the skill explains the result THEN it distinguishes observed diagnostics from checks not reached and never manufactures accepted decisions in throwaway probes

## Success Criteria

```bash
# eval_1: Explain planning blockers without implying completed validation
eval_1() {
  bash tests/test-toolkit-decompose.sh && bash tests/test-toolkit-experience.sh && bash tests/lint-skill-docs.sh && bash tests/lint-docs.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Explain planning blockers without implying completed validation"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3]
    terminal: true
    expected_duration_sec: 120
retry_policy:
  max_iterations: 3
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [code, tests]
  required_tools: [git, bash]
  timeout_minutes: 10
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
- `tasks/done`
- `.taskspec/acceptance`

## Open Questions

(none — this task is fully specified)
