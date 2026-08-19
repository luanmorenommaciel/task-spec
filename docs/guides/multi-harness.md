# Multi-harness execution

Multi-harness means one portable contract, not a fleet scheduler.

```bash
taskspec handoff tasks/T-…-leaf.md --backend codex \
  --out .taskspec/handoffs/codex-attempt.json
```

`TaskHandoff/v3` carries the task revision, HMAC authorization, UUID attempt,
immutable Git base, dependency closure, selected backend, workspace, write
scope, budgets, normalized agent contract, eval command, evidence requirements,
and acceptance command. It contains no credentials or private evaluator
instructions and never starts a model.

Give that file to Codex, Claude Code, Kimi, Grok Build, or a conformant custom
executor. A sealed specific `execution_backend` must match; only
`execution_backend: any` permits selection when issuing the handoff.

Each dispatch receives a fresh attempt ID by default. If you issue separate
Codex and Claude attempts, their receipts and acceptance records cannot be
reused across one another even though they share a task revision.

```bash
taskspec handoff tasks/T-…-leaf.md --backend codex --out codex.json
taskspec handoff tasks/T-…-leaf.md --backend claude --out claude.json
```

Only one resulting attempt should be accepted. Task-Spec does not schedule,
race, merge, or choose among those attempts; that orchestration belongs to a
harness or Converge.

TaskMesh may still pick a **named model** for a leased attempt. Put
`tasks/.mesh/roster.json` (`TaskMeshRoster/v1`) in the repository so effort
bands and optional kinds choose adapter + model out of the box. See
[TaskMesh](../getting-started/taskmesh.md#name-the-model-roster).
