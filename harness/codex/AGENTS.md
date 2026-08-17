# AGENTS.md — using Task-Spec from a Codex host

Task-Spec is the atomic work contract; Codex is a replaceable authoring or
execution harness. Use the installed `task-spec` skill for intent-level requests
and drive deterministic behavior through the `taskspec` CLI.

## Canonical lifecycle

```bash
taskspec init
taskspec setup signing
taskspec plan --manifest tasks/.plans/change.yaml
taskspec batch --plan tasks/.plans/change.yaml
taskspec validate tasks/T-…-leaf.md
taskspec dod tasks/T-…-leaf.md
taskspec gate --stamp tasks/T-…-leaf.md
taskspec handoff tasks/T-…-leaf.md --backend codex --out .taskspec/handoffs/attempt.json
# Execute exactly the authorized handoff.
taskspec accept --handoff .taskspec/handoffs/attempt.json --stamp tasks/T-…-leaf.md
taskspec transition T-…-leaf done
taskspec status T-…-leaf
```

`taskspec new <slug> <effort> [agent]` remains the direct one-task scaffold.
Use format v4 only for approved independent evidence policy. `taskspec graph
--check`, `ready --all`, and `doctor --backlog` are read-only operational views;
they do not schedule work.

## Executor rules

- Execute one `TaskHandoff/v3` attempt. Honor its revision, base commit,
  dependency closure, write surface, budgets, agent contract, and commands.
- Never hand-edit `signed_off*` or `accepted*`. Only the PRE-gate writes HMAC v3
  authorization; only the POST-gate writes `AcceptanceRecord/v1` and the complete
  acceptance envelope.
- Do not expose credentials, private holdouts, or evaluator instructions in a
  TaskPlan, Task-Spec, handoff, or authoring-evidence bundle.
- If the contract must change, stop and request explicit replanning and
  reauthorization. Never create runtime dependency edges or widen scope.
- Respect retry and no-progress limits. Terminal failure parks with context; it
  never loops beyond the signed budget.

## Machine contract

- Exit `0`: success / DELEGATE / ACCEPT.
- Exit `1`: contract, gate, eval, graph, or acceptance rejection.
- Exit `2`: usage error.
- `gate` emits `TIER=1|2`; `accept` emits `ACCEPTED=1|0`; `demo` ends with
  `DEMO=READY`; the complete typed surface is `taskspec agent-context`.
