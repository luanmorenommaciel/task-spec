# Task-Spec quick reference

```bash
taskspec init
taskspec setup signing
taskspec setup

taskspec plan --manifest tasks/.plans/change.yaml
taskspec batch --plan tasks/.plans/change.yaml
taskspec validate tasks/T-*.md
taskspec dod tasks/T-*.md
taskspec gate --stamp tasks/T-…-leaf.md
taskspec handoff tasks/T-…-leaf.md --backend codex --out .taskspec/handoffs/attempt.json
taskspec run --ci tasks/T-…-leaf.md
taskspec accept --handoff .taskspec/handoffs/attempt.json --stamp tasks/T-…-leaf.md
taskspec transition T-…-leaf done
taskspec graph --check
taskspec status T-…-leaf
taskspec doctor --backlog
```

## Frontmatter essentials

```yaml
---
id: T-YYYYMMDD-kebab-slug
title: One-line imperative
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: []
touches_paths: [src/existing.py]
creates_paths: [tests/test_change.py]
source_note: tasks/.plans/change.yaml
created: 2026-08-11T00:00:00Z
tracker_ref: (none)
execution_backend: any
signed_off: false
signed_off_by: (none)
signed_off_at: (none)
accepted: false
accepted_by: (none)
accepted_at: (none)
---
```

XL/XXL nodes add `children: [T-…, T-…]`, use empty write lists, and are not
delegated. XS/S/M/L leaves omit `children`.

## Proof chain

| Step | Positive token | Meaning |
|---|---|---|
| Plan | `TASK_PLAN=OK` | Manifest is complete enough to preview |
| DoD | `DOD=COMPLETE` | Behavior/eval/Exit Check traceability is complete |
| Gate | `TIER=1` or `TIER=2` | Spec is delegate-safe at the reported trust tier |
| Run | exit 0 | Current evals pass |
| Accept | `ACCEPTED=1` | Post-gate passed; `--stamp` may write acceptance |

## Rules to remember

- Write scope is `touches_paths ∪ creates_paths`.
- `status: done` requires `accepted: true`.
- Never hand-edit `signed_off*` or `accepted*`.
- Valid HMAC v1/v2 is supervised Tier 2; re-stamp each active task for v3/TaskRevision coverage.
- Research credentials stay outside every Task-Spec contract.
- `--json`, `--dry-run`, `NO_COLOR`, and `TASKSPEC_COLOR` are global.
