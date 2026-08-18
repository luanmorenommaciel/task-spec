# harness/ — non-normative host surfaces

This directory is **not** the Task-Spec contract. The contract is `../spec/`
plus the conformance suite. Files here tell a specific host or optional pack
how to drive that contract.

## Inclusion rule

A path belongs here only if it is one of:

1. **Host surface** — how a named executor or CI host discovers and runs
   Task-Spec (`engines/`, `claude-code/`, `codex/`, `github-action/`).
2. **Optional pack** shipped with the engine for authoring or assurance
   (`research/`, `mutations/`, `agents/`).
3. **TaskMesh adapter descriptors** (`mesh-adapters/`). These are runtime
   JSON the daemon loads from `$TASKSPEC_HOME/harness/mesh-adapters`. Do not
   move them without changing that lookup, the installer copy, and the
   packaging test.

`trackers/` is a roadmap note, not a shipped integration.

## What does *not* belong here

| Concern | Lives in |
|---|---|
| Normative format, schemas, L0–L2 suite | `../spec/` |
| Python/Bash verbs (`author`, `gate`, `accept`, …) | `../src/` |
| TaskMesh cockpit CLI (Python) | `../src/meshctl/` |
| TaskMesh daemon (Go) | `../mesh/` |
| Shipped mesh image / worker | `../release/mesh/` |

## Claude plugin copies

`.claude-plugin/` at the repository root is the marketplace source of truth.
`claude-code/` is the host-local copy the installer ships with the engine
(`SKILL.md` here is Claude-specific). Keep their versions aligned; the
doc-consistency lint checks both.
