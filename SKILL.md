---
name: task-spec
description: Turn intent, repository evidence, and optional cited research into atomic, signed, self-verifying Task-Specs; preview complete TaskPlan manifests; hand one authorized leaf to any coding harness; and independently accept the result.
license: MIT
metadata:
  version: "3.6.0"
---

# Task-Spec

Use this skill when the user asks to create, decompose, authorize, hand off, run,
or accept atomic agent work. Task-Spec is the unit of work; the harness is a
replaceable executor.

## Operating loop

1. Understand the desired repository outcome and inspect the current code.
2. Use research only when current external evidence is necessary. Provider use
   must be explicit and its output normalized to `AuthoringEvidence/v1`.
3. Compose every declared unit in a `TaskPlan/v1` manifest. Do not invent
   omitted goals, paths, behaviors, evals, dependencies, or children.
4. Preview with `taskspec plan --manifest <file>`. Ask for approval when the
   plan is not already marked `approved: true`.
5. Generate with `taskspec batch --plan <file>`, then run `taskspec validate`
   and `taskspec dod` on every leaf and node.
6. Authorize a leaf only through `taskspec gate --stamp <spec>`. Never edit
   `signed_off*` or `accepted*` by hand.
7. Emit `taskspec handoff <spec> --backend <harness>` and give that read-only
   contract to Codex, Claude Code, Kimi, Grok Build, or another executor.
8. After work, independently run `taskspec accept --stamp <spec>`. Only then may
   the task transition to `done`.

## Atomicity rules

- `XS/S/M/L` are executable leaves. `L` requires a long-horizon backend from
  `TASKSPEC_LONG_HORIZON_BACKENDS` and one coherent done-condition.
- `XL/XXL` are decomposition nodes with at least two/three children. They own
  no write surface and are never handed to an executor.
- Write scope is `touches_paths ∪ creates_paths`. Dependencies must be explicit.
- An eval must discriminate real work from a stub. Existence-only checks need
  explicit supervision or annotation.
- HMAC is tamper evidence from a shared repository key, not author identity,
  sandboxing, or proof that an eval is semantically wise.

## Commands

Run `taskspec agent-context` for the complete machine contract. The common path:

```bash
taskspec init
taskspec setup signing
taskspec plan --manifest tasks/.plans/change.yaml
taskspec batch --plan tasks/.plans/change.yaml
taskspec validate tasks/T-*.md
taskspec dod tasks/T-*.md
taskspec gate --stamp tasks/T-…-leaf.md
taskspec handoff tasks/T-…-leaf.md --backend codex
taskspec accept --stamp tasks/T-…-leaf.md
```

Default output is human-readable. `--json` adds a uniform CLI result envelope;
`--dry-run` prevents supported mutations. Never place provider/model credentials
in a TaskPlan, Task-Spec, TaskHandoff, or AuthoringEvidence document.
