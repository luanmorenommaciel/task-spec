---
name: task-spec
description: |
  Turn intent and repository evidence into native reviewed plans and atomic,
  signed Task-Specs; run authorized recipes with TaskMesh, inspect canonical
  acceptance, and retain release and maintenance evidence.
metadata:
  version: "3.10.0"
---

# Task-Spec for Claude Code

Task-Spec is the atomic contract; Claude Code is a replaceable authoring or
execution harness. The canonical doctrine ships with the installed engine, and
the `taskspec` CLI owns deterministic validation and mutation.

Read current `taskspec agent-context` and task or initiative status before acting.
Use the same product skill and persisted state as other supported harnesses;
conversation history does not authorize work. Detailed workflows are available
through `taskspec guide intent`, `decomposition`, `recipes`, `execution`,
`acceptance`, `sdlc`, and `migration`.

## Prerequisites

The `taskspec` CLI must be on PATH and `taskspec doctor` must pass. Use the
repository installer with `--global` for user-level Claude, Codex/Kimi, and Grok
skills, or `--target <repo>` for project-local copies.

## What to do

1. Inspect repository instructions, the smallest relevant code slice, its tests,
   schemas, and ownership boundaries.
2. Use optional research only when explicitly selected; normalize retained
   results as credential-free `AuthoringEvidence/v1`.
3. Compose every declared unit in `TaskPlan/v1`, preview it, and generate only
   the approved plan. Never invent omitted paths, evals, dependencies, or
   children.
4. Drive the CLI; never hand-edit authorization or acceptance fields:

   | Intent | Command |
   |--------|---------|
   | Prepare native decomposition | `taskspec decompose prepare <initiative> --recipe <file>` |
   | Explicit topology review | `taskspec decompose review <initiative> --accept --reviewer <name> --reason <text>` |
   | Compile reviewed plan | `taskspec decompose compile <initiative>` |
   | Compose and preview | `taskspec plan --manifest <TaskPlan>` |
   | Generate approved units | `taskspec batch --plan <TaskPlan>` |
   | Direct scaffold | `taskspec new <slug> <effort> [agent]` |
   | Prove authoring | `taskspec validate <spec>` then `taskspec dod <spec>` |
   | PRE-gate authorization | `taskspec gate --stamp <spec>` |
   | Portable handoff | `taskspec handoff <spec> --backend claude --out <file>` |
   | POST-gate acceptance | `taskspec accept --handoff <file> --stamp <spec>` |
   | Status and recovery | `taskspec status <id>` and `taskspec doctor --backlog` |
   | Optional TaskMesh cockpit | `taskspec mesh frontier`, `run`, `watch`, `accept`, and `finish` |
   | Managed recipe or native graph | `taskspec mesh run --initiative <id> --execute` |
   | Opt-in evidence task | `taskspec new --format 4 <slug> <effort>` then `taskspec author-doctor <spec>` |

5. Respect the effort gate: XS/S/M/L are runnable leaves; L needs a backend
   from `TASKSPEC_LONG_HORIZON_BACKENDS`. XL/XXL are non-runnable nodes with at
   least two/three child Task-Specs.

## Hard rules

- `signed_off: true` comes ONLY from `taskspec gate --stamp`. Never hand-stamp
  the envelope; HMAC v3 seals `TaskRevision/v1` and unknown authority fields.
- A task is DONE only when `taskspec accept` emits `ACCEPTED=1` — an agent's
  own claim of GREEN is not evidence. Acceptance must bind `TaskHandoff/v3`, the
  attempt, base commit, closure, repository scope, and required receipts.
- Format v4 acceptance must receive every policy-required external receipt;
  never expose a private holdout bundle to the executor.
- Changed scope or proof policy requires explicit replanning and reauthorization;
  never silently rewrite downstream dependencies.
- Resolve recipe guidance before sealing. Managed recipes use bounded sequential
  rounds in the existing TaskMesh lifecycle, including one-task graphs. Workers
  cannot sign or accept their own work. Reuse applicable recorded decisions and
  ask only for missing decisions or authorization.
- An incident becomes candidate work. Pipeline success is reported evidence;
  it does not establish target health or authorize deployment.
- Exit codes: `0` pass/accept · `1` failed/rejected · `2` usage error.
- When TaskMesh is installed, Claude may start or reconnect to the durable
  cockpit, but the daemon owns the run and Task-Spec owns authority. Do not call
  a supervised worktree a sandbox, self-accept an attempt, or merge the target
  branch. Autonomous OMP requires externally verified isolation and expiring
  credential evidence.
