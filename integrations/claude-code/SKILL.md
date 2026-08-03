---
name: task-spec
description: |
  Author and gate atomic, self-verifying task-specs via the taskspec CLI. Use
  when the user says "create a task", "scaffold a task", "make this executable",
  "decompose this into work", "turn this into a backlog", "convert this legacy
  task", or mentions Task-Spec, EDD, or eval-driven development. Produces
  T-*.md specs with runnable bash evals + a behavior-to-eval traceability chain
  + a post-execution acceptance gate that any conformant engine can crank.
  Best for XS/S/M-effort work with a machine-checkable done-condition;
  L runs on GLM (one coherent goal), routes XL or subjective work to SDD.
metadata:
  version: "3.3.0"
---

# task-spec (thin skill)

This is a **thin delegating skill**: the doctrine lives in the task-spec engine
repo, the mechanics live in the `taskspec` CLI. The skill's job is to (a) fire
on authoring intent and (b) point the agent at the right commands.

## Prerequisites

The `taskspec` CLI on PATH (`taskspec doctor` must PASS). If it is missing,
clone the engine repo and symlink `bin/taskspec` onto PATH — see the repo
README.

## What to do

1. **Read the authoring doctrine** — `docs/authoring-workflow.md` in the
   task-spec engine repo (the 9-phase loop: understand → research → scan →
   architect → compose → validate → gate → dispatch → accept). It is the
   normative workflow; this skill only routes to it.
2. **Drive the CLI**, never hand-edit envelope fields:

   | Intent | Command |
   |--------|---------|
   | Scaffold a spec | `taskspec new <slug> <effort> [agent] [source_note]` |
   | Bulk scaffold | `taskspec batch --intent-file <f> --effort S\|M` |
   | Structural lint | `taskspec validate [--shellcheck-evals] <spec>` |
   | PRE-gate + sign off | `taskspec gate --stamp <spec>` |
   | Run evals (JSON) | `taskspec run --ci <spec>` |
   | POST-gate accept | `taskspec accept --stamp [--gold-sanity] <spec>` |

3. **Respect the effort gate**: XS/S/M proceed; L only with
   `execution_backend: glm` and one coherent done-condition; XL or subjective
   output → route to SDD, do not author a task-spec.

## Hard rules

- `signed_off: true` comes ONLY from `taskspec gate --stamp`. Never hand-stamp
  the envelope; hand-stamping is rejected by the sign-off envelope check.
- A task is DONE only when `taskspec accept` emits `ACCEPTED=1` — an agent's
  own claim of GREEN is not evidence.
- Exit codes: `0` pass/accept · `1` failed/rejected · `2` usage error.
