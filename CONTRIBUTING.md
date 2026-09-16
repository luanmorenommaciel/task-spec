# Contributing

Humans and coding agents follow the same contract: [AGENTS.md](AGENTS.md).

## Before you start

Read [OPERATING.md](OPERATING.md) for the hop order and [docs/index.md](docs/index.md)
for the knowledge base. The normative contract is [`spec/`](spec/README.md) plus the
conformance suite; everything under `docs/` explains it rather than defining it.

## The gate

```bash
make check
```

This runs the same doctor, lint, test, and conformance legs as hosted CI on Ubuntu
and macOS. Run it before considering a change done. A passing local run is evidence
for your working tree, not a release decision.

| Change | Also update |
|---|---|
| Task format or schema | Schemas, conformance fixtures, and [CHANGELOG.md](CHANGELOG.md) together |
| Root `SKILL.md` | The byte-for-byte mirror at [`skills/task-spec/SKILL.md`](skills/task-spec/SKILL.md) |
| A new top-level directory or root file | The layout table in [AGENTS.md](AGENTS.md) and the manifest in `tests/test-repo-layout.sh` |
| Any command shown in [README.md](README.md) | Its proof entry in [`docs/readme-command-coverage.json`](docs/readme-command-coverage.json) |
| CLI commands or metadata | Regenerate `docs/reference/cli.md` with `python3 tools/render-cli-reference.py --write docs/reference/cli.md` |

## What never gets rewritten

Frozen artifacts record what actually shipped. Do not edit them to match a later
refactor, and do not fix stale relative links inside them:

- `release/<version>/` — per-version release and qualification evidence
- `.taskspec/acceptance/` — canonical acceptance receipts
- `tasks/done/`, `tasks/parked/` — accepted and parked task history

## Reporting problems

Security reports belong in [SECURITY.md](SECURITY.md), not in a public issue.

## Contributors

Maintained by Luan Moreno Medeiros Maciel.

TaskSpec is built and dogfooded with coding agents working under its own contract.
The engine's backlog in [`tasks/`](tasks/README.md) records which agent executed each
accepted leaf, and [`release/`](release/README.md) retains the evidence, including the
runs that failed review.

| Agent | Role in this repository |
|---|---|
| Claude Code | Authoring, execution through the `claude-native` adapter, and chat-behavior qualification |
| Codex | Authoring, execution through the `codex-native` adapter, and release supervision |
| Kimi | Dispatch harness target; see [`harness/engines/kimi.md`](harness/engines/kimi.md) |

Agent work is held to the same boundary as human work. No worker seals its own task,
no worker accepts its own result, and no agent merges the user branch.
