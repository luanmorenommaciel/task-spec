# Agent entry

Before any task, read [OPERATING.md](OPERATING.md).
Do not invent a second loop.
Do not skip the HMAC seal.
Do not put family hops in docs/.

# AGENTS.md — contributing to the task-spec engine

This repo is the **task-spec engine**: an open, vendor-neutral, self-verifying
unit-of-work format (markdown + YAML frontmatter + runnable bash evals) plus the
bash toolchain that authors, gates, dispatches, and accepts those tasks. It was
extracted from `converge/skills/task-spec` at v3.3.0 and now stands alone.

## Repository layout

| Path | Holds |
|---|---|
| `bin/taskspec` | the one CLI entry point; dispatches to `src/` |
| `spec/` | **normative**: the v3/v4 format, JSON schemas, conformance suite |
| `interop/` | `UPSTREAM.lock` — protocol version/commit/digest lock. Path is frozen by 3.8.1 evidence; do not move it |
| `src/` | the Python + Bash engine, one directory per verb, plus `src/templates/` |
| `src/meshctl/` | Python TaskMesh cockpit (`taskspec mesh`); not the Go daemon |
| `mesh/` | the optional Go control plane (`mesh/cmd/`, `mesh/internal/mesh/`) |
| `harness/` | non-normative host surfaces; see `harness/README.md` for the inclusion rule |
| `tests/` | the self-test suite, all fixtures under `tests/fixtures/`, benchmark cases in `tests/evals/` |
| `release/` | shipped runtime inputs and frozen per-version evidence; see `release/README.md` |
| `docs/` | the knowledge base; start at `docs/index.md`. New how-tos go in `docs/guides/`; `docs/runbooks/` is closed |
| `tools/` | repository scripts: release builders, renderers, signing-key provisioner |
| `tasks/`, `.taskspec/` | this repo's own dogfooded backlog and acceptance receipts — not the public tutorial; see `tasks/README.md` |
| `skills/` | the in-repo skill pack; `skills/task-spec/SKILL.md` is a byte-for-byte copy of root `SKILL.md`, enforced by `tests/test-repo-layout.sh` |
| `assets/` | README images only |
| `.claude-plugin/` | marketplace source of truth for the Claude plugin |
| `.github/` | workflows and dependabot config |
| `CONTRIBUTING.md`, `SECURITY.md` | human entry points; agents still follow this file |

Frozen artifacts under `release/<version>/`, `.taskspec/acceptance/`, and
`tasks/done/` describe what actually shipped. Never rewrite them to match a
later refactor.

`tests/test-repo-layout.sh` enforces this table: the set of top-level
directories and root files is declared there, and adding either one requires
updating the test and this table in the same change. That is deliberate — it
is what keeps the tree from drifting back into twenty-odd top-level
directories.

## Build / test

There is no build step — the engine is bash + markdown. The single release gate
(hosted CI runs exactly this on ubuntu-latest; run it on macOS locally before
touching the bash-3.2 gate path, because no hosted runner covers that any more):

```bash
make check            # doctor + lints + all self-tests + conformance
```

Or run the pieces individually:

```bash
bash bin/taskspec doctor                       # toolchain sanity (bash, git, crypto, key)
bash tests/lint-skill-docs.sh                  # VERSION == CHANGELOG == _lib.sh
bash tests/lint-docs.sh                        # markdown links resolve, fences balanced
for t in tests/test-*.sh; do bash "$t"; done   # full self-test suite
bash spec/conformance/run_conformance.sh       # conformance suite (default self-adapter)
bash bin/taskspec conformance --self-test      # L0–L2 against the bundled ref executor
```

All of the above must be green before a change is considered done.

## Conventions

- **bash-3.2 floor on the core gate path.** No bash-4-only constructs
  (`declare -A`, `mapfile`/`readarray`) in `src/gate/`, `src/accept/`, or
  `src/lib/`. macOS system bash 3.2.57 must run them. Aux scripts that need
  bash 4 (e.g. `src/backlog/lint-backlog.sh`) must call `ts_require_bash4`.
  `tests/test-bash-portability.sh` enforces this.
- **VERSION is the single version source.** Bump `VERSION`, mirror it in
  `src/lib/_lib.sh:TASKSPEC_VERSION`, and add a CHANGELOG entry — the lint
  asserts all three agree.
- **Format changes are triple-locked.** Any change to the spec format requires:
  the JSON Schemas in `spec/schemas/` updated, conformance fixtures in
  `spec/conformance/` updated, and a CHANGELOG entry. `format_version` bumps
  are MAJOR.
- **Scripts resolve everything relative to their own location** (via
  `src/lib/_lib.sh`). Never hardcode absolute paths.
- Keep edits minimal and in the style of the surrounding file.

## Boundaries

- `harness/` (engines, trackers, adapters) is **non-normative** — the contract is
  `spec/` + the conformance suite. Adapters may lag; the spec may not.
- `tests/fixtures/diamond-6/` are CI fixtures: never `--stamp` or otherwise mutate
  their frontmatter sigs in tests.
- **No git mutations** (commit/push/reset/rebase) unless the user explicitly
  asks. Leave the working tree for review.
