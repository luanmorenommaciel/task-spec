---
id: T-20260916-chat-workspace-paths
title: "Keep planning and authoring scratch inside the harness workspace"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 3
agent: codex
parent: (none)
depends_on: [T-20260914-toolkit-experience]
supersedes: (none)
touches_paths: [SKILL.md, skills/task-spec/SKILL.md]
creates_paths: []
source_note: "User-authorized full release completion and retained Claude planning denial, 2026-09-15"
created: "2026-09-16T02:44:15Z"
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
signed_off_at: 2026-09-16T02:46:46Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:74f8bded6892ac93ff97a6ddf12c4f33e3382cee0a9cf52c937d12ccadbe9170
---

# Keep planning and authoring scratch inside the harness workspace

> **Why:** The retained planning observation chose /tmp examples and then hit the native restricted Read boundary. Make the workspace rule apply before every workflow route.

## Goal

Make the skill entry point require workspace-contained examples and scratch on every route. Explain that shell access does not grant native file-tool access, preserve the denial stop rule, and keep the root and in-repository skill identical. This task delivers reviewed guidance; it does not qualify provider behavior.

## Context

The user explicitly authorized completing the full release. This bounded documentation correction follows release/3.10.0/qualification/completion-retry/chat/runs/plan-claude-20260916T022738Z/behavior-review.json. It does not authorize another live provider attempt after the new denial. Preserve historical evidence, signatures, runtime permissions and the original release criteria.

## Behavior

- **B-1** — GIVEN any planning or atomic-authoring request WHEN the skill chooses example or scratch paths THEN its shared instructions select paths inside the current workspace before tool execution, retain the denial stop rule, and remain identical in both entry points

## Success Criteria

```bash
# eval_1: Keep planning and authoring scratch inside the harness workspace
eval_1() {
  bash tests/test-toolkit-experience.sh && bash tests/lint-skill-docs.sh && bash tests/lint-docs.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Keep planning and authoring scratch inside the harness workspace"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
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
