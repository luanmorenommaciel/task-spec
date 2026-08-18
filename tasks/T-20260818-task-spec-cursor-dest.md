---
id: T-20260818-task-spec-cursor-dest
title: "Install Task-Spec skill into Cursor"
status: ready
format_version: 3
profile: full
effort: M
budget_iterations: 5
agent: wright
parent: (none)
depends_on: []
supersedes: (none)
children: []
touches_paths:
  - install.sh
  - docs/getting-started/installation.md
  - tests/test-v36-experience.sh
creates_paths: []
source_note: "Luan 2026-08-18: stamp real chat-pack gaps. Task-Spec install dests are .agents, .claude, .grok. Cursor dest is missing. Range inventory 2026-08-18."
created: "2026-08-18T15:20:00Z"
tags: ["task-spec", "chat-pack", "cursor"]
owner: wright
priority: P1
severity: feature
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: (none)
source_action_item: (none)
tracker_ref: (none)
execution_backend: none
signed_off: true
signed_off_by: luan-moreno
signed_off_at: 2026-08-18T15:08:26Z
accepted: false
accepted_by: (none)
accepted_at: (none)
---

# Install Task-Spec skill into Cursor

> **Why:** `install.sh` already copies the skill to Codex/Kimi, Claude, and Grok. Cursor is the missing dest. Range cannot see the chat door there.

## Goal

Add `$TARGET/.cursor/skills/task-spec` to the same install loop as the other three dests. Prove it in the existing dest test. Do not add new skills. Do not add product verbs.

## Context

Read `install.sh` and `tests/test-v36-experience.sh`. Current dests:

- `$TARGET/.agents/skills/task-spec`
- `$TARGET/.claude/skills/task-spec`
- `$TARGET/.grok/skills/task-spec`

`--global` uses HOME as TARGET. The Cursor dest is the same relative path: `.cursor/skills/task-spec`.

Root `SKILL.md` stays the source copied into every dest. Do not invent a second skill body.

## Behavior

- B-1 — GIVEN `install.sh --copy` into a temp target WHEN it finishes THEN `$TARGET/.cursor/skills/task-spec/SKILL.md` exists and matches the other three dests
- B-2 — GIVEN `install.sh --global --copy` WHEN it finishes THEN `$HOME/.cursor/skills/task-spec/SKILL.md` exists
- B-3 — GIVEN `docs/getting-started/installation.md` WHEN read THEN it names Cursor next to Codex/Kimi, Claude, and Grok
- B-4 — GIVEN `tests/test-v36-experience.sh` WHEN run THEN it fails if Cursor dest is missing or drifts

## Anti-Patterns

- Adding a `skills/` pack in this leaf (that is T-20260818-task-spec-skills-pack)
- Dropping Codex, Claude, or Grok dests
- Inventing new CLI verbs
- Copying Converge passes
- Importing another Sealworks unit
- Writing to Nexo

## Do-Not-Touch

- `VERSION`
- `SKILL.md`
- `bin/taskspec`
- `src/`
- `spec/`
- `README.md`
- mesh / TaskMesh
- Other Sealworks repositories
- Nexo vault

## Open Questions

- None. Add the missing Cursor dest only.

## Observability Hooks

- `tests/test-v36-experience.sh` fails if Cursor dest is missing
- `cmp` of dest `SKILL.md` files fails on drift

## Success Criteria

```bash
eval_1() {
  bash tests/test-v36-experience.sh
}

eval_2() {
  python3 -c "
from pathlib import Path
text = Path('docs/getting-started/installation.md').read_text(encoding='utf-8')
src = Path('install.sh').read_text(encoding='utf-8')
assert '.cursor/skills/task-spec' in text
assert '.cursor/skills/task-spec' in src
print('cursor dest named')
"
}
```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: dest test proves Cursor alongside the other three
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-4]
    terminal: true
    expected_duration_sec: 60
  - id: eval_2
    description: install.sh and installation.md name Cursor dest
    runnable: bash
    check_type: deterministic
    verifies: [B-3]
    terminal: true
    expected_duration_sec: 5
retry_policy:
  max_iterations: 5
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [code, tests]
  required_tools: [git, bash]
  timeout_minutes: 20
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1 && eval_2
```

## Rollback Plan

Revert only the declared write surface and park the task with context. Do not merge. Do not invent a stamp or HMAC.
