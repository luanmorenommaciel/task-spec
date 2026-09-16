# Proposal: one lifecycle contract for the Supervised Agentic Loop

Status: draft. Not normative. Nothing under `spec/` changes until this is
accepted and shipped with schema, conformance fixture, and changelog together.

## Problem

The chat skill answers "what is next" by reading CLI state, not conversation
history. Today that state comes from three contracts with one shared idea and
no shared shape:

| Contract | Producer | `state` values | Next-step field |
|---|---|---|---|
| `TaskStatus/v1` | `src/backlog/status.py` | `ready`, `in-progress`, `blocked`, `done`, `parked` | `next_command` (exactly one) |
| `TaskDecompositionResult/v1` | `src/decompose/cli.py` | `intent`, `needs_review`, `compiled` | `next` (list) |
| `TaskInitiativeStatus/v1` | `src/decompose/cli.py` **and** `src/cli/initiative.py` | decompose side: `intent`, `needs_review`, `reviewed`, `blocked`, `compiled`; initiative side: always `compiled` | `next` (list) |

Observed on 2026-09-16 in the working tree:

- `TaskInitiativeStatus/v1` has two producers and no schema in `spec/schemas/`.
- `src/cli/initiative.py` reports `state: compiled` even when every task is
  accepted and every capability is proven. The phase after compilation is only
  visible by reading `accepted_tasks`, `attempts`, and `proof_gaps` together.
- `TaskStatus/v1` has a schema and exactly one `next_command`. It is the model
  to follow.

So the chat has to infer the phase from several fields. A fresh harness, or a
different harness, must reproduce that inference. That is the gap.

## Proposal

Publish `TaskInitiativeStatus/v2` with an explicit `phase` enum covering the
whole loop, one producer, and one safe `next_command` plus optional
`next_options`. Keep `TaskStatus/v1` unchanged as the per-task view.

### Phase enum and its evidence

Each phase is derived from files on disk, never from conversation. The
"decides" column is the human decision that moves the initiative forward. The
"next_command" column is what the CLI must return.

| Phase | Derived from | Who decides next | `next_command` |
|---|---|---|---|
| `intent` | `tasks/.plans/<id>/intake.md` exists, no `delivery-plan.yaml` | author writes the recipe | `taskspec decompose prepare <id> --recipe <file>` |
| `proposed` | `delivery-plan.yaml` exists, no `reviews/delivery-plan-review.json` | human reviewer | `taskspec decompose review <id> --accept --reviewer <name> --reason <text>` |
| `reviewed` | review signature verifies, no `bundle.json` | none, mechanical | `taskspec decompose compile <id>` |
| `compiled` | `bundle.json` verifies, some units not under `tasks/` | none, mechanical | `taskspec batch --plan tasks/.plans/<id>/task-plan.json` |
| `materialized` | all units exist, some not Tier 1 or stale | human authorizer | the failing task's `TaskStatus/v1.next_command`, normally `taskspec gate --stamp <spec>` |
| `sealed` | all units Tier 1, no live attempt, not all accepted | human starts execution | `taskspec mesh run --initiative <id> --execute` |
| `executing` | any lease in `leased`, `preparing`, `running`, `verifying` | TaskMesh | `taskspec mesh status <attempt>` |
| `awaiting_supervision` | any lease in `awaiting_supervision` | supervisor | `taskspec mesh accept <attempt>` |
| `parked` | a stopped attempt whose task is not accepted | human resolves blocker | `taskspec mesh explain <attempt>` |
| `accepted` | all tasks accepted, some capability unproven | author adds proof task or human accepts gap | `taskspec graph --initiative <id> --view capabilities` |
| `proven` | all capabilities proven | release decision in your CI/CD | `taskspec guide sdlc` |
| `blocked` | integrity or source failure in any phase | human | the recovery command reported by the failing check |

Rules that hold in every phase:

- `next_command` is exactly one string and must be safe to run in a read-only
  request. Mutating commands appear in `next_options`, never in `next_command`,
  unless the phase requires a human decision and the command is the decision
  itself, as with `review --accept` and `gate --stamp`.
- `phase` never advances on a model's claim. It is recomputed from disk and the
  Mesh database every call.
- `blocked` beats every other phase. Diagnostics carry the failing check.
- The contract never carries signing material or private eval instructions.

### Draft schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TaskInitiativeStatus/v2",
  "type": "object",
  "additionalProperties": false,
  "required": ["contract", "initiative", "phase", "decision_owner", "sources", "tasks", "capabilities", "attempts", "diagnostics", "next_command", "next_options"],
  "properties": {
    "contract": {"const": "TaskInitiativeStatus/v2"},
    "initiative": {"type": "string", "minLength": 1},
    "phase": {"enum": ["intent", "proposed", "reviewed", "compiled", "materialized", "sealed", "executing", "awaiting_supervision", "parked", "accepted", "proven", "blocked"]},
    "decision_owner": {"enum": ["author", "reviewer", "authorizer", "supervisor", "mesh", "release", "none"]},
    "sources": {
      "type": "object",
      "description": "Paths and digests the phase was derived from, so another harness can re-derive it.",
      "additionalProperties": false,
      "required": ["plan_dir", "bundle_digest", "review_verified", "mesh_db"],
      "properties": {
        "plan_dir": {"type": "string"},
        "bundle_digest": {"type": ["string", "null"], "pattern": "^sha256:[0-9a-f]{64}$"},
        "review_verified": {"type": "boolean"},
        "mesh_db": {"type": ["string", "null"]}
      }
    },
    "tasks": {"type": "array", "items": {"$ref": "task-status.schema.json"}},
    "capabilities": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["leg", "seam", "swimlane", "tasks", "proof_tasks", "state", "gap"],
        "properties": {
          "leg": {"type": "string"},
          "seam": {"type": "string"},
          "swimlane": {"type": "string"},
          "tasks": {"type": "array", "items": {"type": "string"}},
          "proof_tasks": {"type": "array", "items": {"type": "string"}},
          "state": {"enum": ["proven", "unproven"]},
          "gap": {"type": ["string", "null"]}
        }
      }
    },
    "attempts": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["task_id", "attempt_id", "state", "fencing_token"],
        "properties": {
          "task_id": {"type": "string"},
          "attempt_id": {"type": "string"},
          "state": {"type": "string"},
          "fencing_token": {"type": ["integer", "string"]}
        }
      }
    },
    "diagnostics": {"type": "array", "items": {"type": "object", "required": ["code", "message"], "properties": {"code": {"type": "string"}, "message": {"type": "string"}}}},
    "next_command": {"type": "string", "minLength": 1},
    "next_options": {"type": "array", "items": {"type": "string", "minLength": 1}}
  }
}
```

### Example

```json
{
  "contract": "TaskInitiativeStatus/v2",
  "initiative": "payments",
  "phase": "materialized",
  "decision_owner": "authorizer",
  "sources": {
    "plan_dir": "tasks/.plans/payments",
    "bundle_digest": "sha256:0f3c…",
    "review_verified": true,
    "mesh_db": null
  },
  "tasks": ["…three TaskStatus/v1 objects…"],
  "capabilities": [
    {"leg": "one deterministic state per payment", "seam": "curated payment state", "swimlane": "data platform", "tasks": ["T-…-merge"], "proof_tasks": ["T-…-integration"], "state": "unproven", "gap": "required task acceptance is missing"}
  ],
  "attempts": [],
  "diagnostics": [],
  "next_command": "taskspec gate --stamp tasks/T-20260916-merge.md",
  "next_options": ["taskspec validate tasks/T-20260916-merge.md", "taskspec dod tasks/T-20260916-merge.md"]
}
```

## How the chat uses it: the session bootstrap

This is the persistent-memory answer. Memory is not in the transcript. It is
three reads at the start of every session, in this order, on any harness:

1. `taskspec agent-context` returns `TaskSpecAgentContext/v1`: the command
   registry, exit codes, and the schema catalogue. This is the shared toolkit.
2. `taskspec status --initiative <id>` returns this contract. `phase` says where
   the loop is. `decision_owner` says whose turn it is. `next_command` says
   what to run.
3. Only if the phase needs a human decision does the chat ask a question, and
   it asks about that decision only. Everything else it runs.

The reply shape stays the one the chat guide already defines: outcome, current
state, evidence or blocker, next action.

## What this contract must not do

- It does not advance a phase. Only the existing commands do, each with its
  own signature or record.
- It does not replace `TaskStatus/v1`. Per-task truth stays per task.
- It does not let a model write it. It is derived on every call from disk and
  the Mesh database.
- It does not carry keys, holdout commands, or evaluator private instructions.

## Grounding

The pattern is established, not invented here.

- Anthropic, "Building effective agents": agents should gain "ground truth
  from the environment at each step" and "pause for human feedback at
  checkpoints or when encountering blockers". `phase` plus `decision_owner`
  encode exactly those checkpoints.
- Anthropic, "Effective context engineering for AI agents" (2025-09-29):
  "Structured note-taking, or agentic memory, is a technique where the agent
  regularly writes notes persisted to memory outside of the context window."
  The plan directory, task files, and acceptance records are that memory, and
  this contract is the index over them.
- Anthropic, "Effective harnesses for long-running agents" (2025-11-26): a
  progress file and a JSON feature list, read at the start of every session,
  because "the model is less likely to inappropriately change or overwrite JSON
  files compared to Markdown files." Same reason this contract is JSON and is
  derived, not written.
- Agent-native CLI practice: the `agcli` framework and the `cli-design` skill
  both put a `next_actions` field in every response so the agent knows what to
  run next. `TaskStatus/v1.next_command` already does this per task. This
  proposal extends it to the initiative.

## Implementation notes

Per `AGENTS.md`, a contract change ships schema, conformance fixture, template
or producer, validator, example, and changelog together. Concretely:

1. Add `spec/schemas/task-initiative-status.schema.json` (this draft).
2. Make `src/cli/initiative.py` the single producer. `decompose status` calls
   it for every phase, not only `compiled`.
3. Add one conformance fixture per phase under `spec/conformance/`.
4. Register the contract in `src/dispatch/agent-context.py`.
5. Keep `TaskInitiativeStatus/v1` readable for one release and note the
   change in `CHANGELOG.md`.
