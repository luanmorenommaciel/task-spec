# Converge donor map

Task-Spec 3.5.0 used `converge@f78f077` as an immutable donor snapshot. The
standalone repository is the authority after the port; this table records where
the portable behavior came from and where it now lives. It is provenance, not a
runtime dependency.

| Capability | Donor files at `converge@f78f077` | Canonical Task-Spec result |
|---|---|---|
| Six-tier sizing, L routing, XL/XXL composition | `skills/task-spec/scripts/_lib.sh`, `validate-task-spec.sh`, `templates/task-spec.md.tpl`, `references/concepts/effort-gate.md`, `tests/test-effort-sizing.sh` | `src/lib/_lib.sh`, `src/gate/validate-task-spec.sh`, template, schema, guide, and sizing suite |
| Write-surface union and collision analysis | `_lib.sh`, `validate-task-spec.sh`, `lint-backlog.sh` | Portable `touches_paths` plus `creates_paths` budgets, dual-create failures, shared-write reports, and concurrency groups |
| HMAC authorization envelope | `_lib.sh`, `safe-to-delegate.sh`, `validate-task-spec.sh`, `accept-task.sh`, `tests/test-hmac-envelope.sh` | Donor v2 parity plus upstream HMAC v3/TaskRevision hardening; v1/v2 remain authentic-but-narrow Tier 2 |
| Worktree and eval workspace correctness | `_lib.sh`, `run-task-spec.sh`, signing-key setup | Git common-directory key lookup and task-workspace-relative eval execution |
| Stub resistance and validation purity | `safe-to-delegate.sh`, `validate-task-spec.sh` | Existence-only eval detection, supervised override, and `validate --no-state` |
| Dependency frontier and backlog analysis | `list-ready.sh`, `lint-backlog.sh`, `rebuild-state.sh` | Dependency-aware `ready`, `--all`, dangling/cycle failures, conflicts, and deterministic derived state |
| Settlement and tracker compatibility | `transition-status.sh`, `accept-task.sh`, template | `done` requires `accepted: true`; portable `tracker_ref` replaces vendor-specific backlinks while `linear_ref` remains readable |
| Safe generation and metrics | `generate-task-spec.sh`, `batch-generate.sh`, `_lib.sh`, backlog scripts | Non-interpolating rendering and JSON-safe metrics in the standalone layout |
| Definition of Done | `definition-of-done.sh` | `taskspec dod` behavior-to-eval-to-exit-check matrix |
| Planning preview | `plan-tasks.py` and Converge Pass-5 tests | Neutral, deterministic `TaskPlan/v1` preview and approved scaffold generation |
| Installation and skill surface | `scripts/install.sh`, `SKILL.md`, `agents/task-architect.md`, runbooks | Multi-harness non-clobbering installer, canonical root skill, compatibility task architect, and new docs front |

Converge-only receipt locations, `cvg/tasks` paths, tracker orchestration, loops,
Cockpit, and Manager behavior were deliberately excluded. Converge receives a
generated mirror through `tools/export-converge.py`; its `UPSTREAM.lock` records
the release, donor baseline, source state, mapped paths, and SHA-256 hashes.
