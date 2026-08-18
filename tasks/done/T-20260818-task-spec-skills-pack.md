---
id: T-20260818-task-spec-skills-pack
title: "Add Task-Spec skills/ pack"
status: done
format_version: 3
profile: full
effort: M
budget_iterations: 5
agent: wright
parent: (none)
depends_on:
  - T-20260818-task-spec-cursor-dest
supersedes: (none)
children: []
touches_paths:
  - README.md
creates_paths:
  - skills/README.md
  - skills/task-spec/SKILL.md
source_note: "Luan 2026-08-18: Task-Spec chat/skills should match Converge pack shape. Converge does not install a mirrored Task-Spec skill. Matching Converge means skills/ plus one product skill, not the 11-pass chain."
created: "2026-08-18T15:20:00Z"
tags: ["task-spec", "chat-pack", "skills"]
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
signed_off_at: 2026-08-18T15:08:27Z
accepted: true
accepted_by: luan-moreno
accepted_at: 2026-08-18T17:09:46Z
accepted_tier: 2
accepted_attempt_id: d7460759-053c-52e4-a87e-6fff072249fc
accepted_authorization_ref: None
acceptance_record_digest: sha256:503ae628b8690551f6ad420bb5d87d14e8675e64ced4a632c05a0037a44492f0
---

# Add Task-Spec skills/ pack

> **Why:** Task-Spec is skill-only at repo root. Converge and Seamwise ship a `skills/` pack. Range asked for that chat interface. Do not invent Converge passes.

## Goal

Add `skills/task-spec/SKILL.md` as a pack copy of root `SKILL.md`, plus `skills/README.md` that names the one product skill and the install dests. Do not add hop skills. Do not change `install.sh` in this leaf.

## Context

Read root `SKILL.md` and `README.md` dest table. Cursor dest is T-20260818-task-spec-cursor-dest. This leaf depends on that dest existing so README can name all four dests honestly.

Converge consumes the external `taskspec` CLI and does not install a mirrored Task-Spec skill. Matching Converge means a `skills/` directory with one product skill, not `idea-to-brd` or swimlanes.

Root `SKILL.md` stays the authoring source. The pack file must match it byte-for-byte.

## Behavior

- B-1 — GIVEN `skills/task-spec/SKILL.md` WHEN read THEN it matches root `SKILL.md` byte-for-byte and has `name: task-spec`
- B-2 — GIVEN `skills/` WHEN listed THEN it contains only `task-spec` plus `README.md`
- B-3 — GIVEN `skills/README.md` and root `README.md` WHEN read THEN they name the pack and the four dests (`.agents`, `.claude`, `.grok`, `.cursor`)

## Anti-Patterns

- Adding Converge pass skills
- Inventing new CLI verbs
- Touching `install.sh` in this leaf
- Drifting the pack away from root `SKILL.md`
- Importing another Sealworks unit
- Writing to Nexo

## Do-Not-Touch

- `VERSION`
- `install.sh`
- `bin/taskspec`
- `src/`
- `spec/`
- `tests/test-v36-experience.sh`
- mesh / TaskMesh
- Other Sealworks repositories
- Nexo vault

## Open Questions

- None. One product skill. No Converge chain.

## Observability Hooks

- `cmp` of root `SKILL.md` and pack `SKILL.md` fails on drift
- extra folders under `skills/` fail eval_2

## Success Criteria

```bash
eval_1() {
  python3 -c "
from pathlib import Path
root = Path('SKILL.md').read_bytes()
pack = Path('skills/task-spec/SKILL.md').read_bytes()
assert root == pack
assert b'name: task-spec' in pack
print('pack matches root')
"
}

eval_2() {
  python3 -c "
from pathlib import Path
names = sorted(p.name for p in Path('skills').iterdir() if p.name != 'README.md')
assert names == ['task-spec'], names
text = Path('README.md').read_text(encoding='utf-8') + Path('skills/README.md').read_text(encoding='utf-8')
for dest in ('.agents/skills/task-spec', '.claude/skills/task-spec', '.grok/skills/task-spec', '.cursor/skills/task-spec'):
    assert dest in text, dest
print('one skill, four dests named')
"
}
```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: pack SKILL.md matches root SKILL.md
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 5
  - id: eval_2
    description: skills/ is one product skill and dests are named
    runnable: bash
    check_type: deterministic
    verifies: [B-2, B-3]
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
  required_tools: [git, bash, python3]
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
