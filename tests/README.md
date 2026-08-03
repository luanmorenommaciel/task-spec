# task-spec engine — Self-Test Suite

## Running the tests

From the engine repo root:

```bash
bash tests/test-task-spec-skill.sh            # default e2e walkthrough
bash tests/test-task-spec-skill.sh --suite all
for t in tests/test-*.sh; do bash "$t"; done  # everything
```

The suite is fully self-contained and runs in a temporary directory. It does **not**
read or write a real `tasks/` backlog.

## Test scripts (7)

| Script | Covers |
|--------|--------|
| `test-task-spec-skill.sh` | End-to-end author flow (generate → validate → transition → rebuild → archive); `--suite fixtures` / `--suite hmac` / `--suite conformance` selectors |
| `test-hmac-envelope.sh` | Key-optional HMAC sign-off envelope: Tier-1/2/3 degrade, injection-safe field writes, `.git/info` key fallback |
| `test-extractor-fuzz.sh` | Adversarial fuzz of the extract-and-run path (heredoc-heavy bodies; never-hang / never-leak-raw-error invariants) |
| `test-bash-portability.sh` | bash-3.2 floor: core gate path under `src/` + conformance runner carry no bash-4-only constructs |
| `test-portability-e2e.sh` | Fresh-install smoke test (`src/lib/install.sh`) + cross-engine equivalence (Python vs TypeScript reference consumers) + schema fidelity |
| `test-v3-closed-loop-e2e.sh` | v3 closed loop: author → gate → dispatch → execute → `accept-task.sh` |
| `lint-skill-docs.sh` | Version consistency: `VERSION` == latest `CHANGELOG.md` heading == `src/lib/_lib.sh:TASKSPEC_VERSION` |

## Conformance suite

The executor-conformance suite moved to **`spec/conformance/`** (it is part of
the published spec, not just a test): **6** `T-conformance-*.md` fixtures (one
per contract clause), the reference driver `run_conformance.sh`, and the
reference self-adapter `adapters/self.sh`. See
[../spec/conformance/README.md](../spec/conformance/README.md) for the vendoring
protocol. Run it via `taskspec conformance --self-test` or
`bash spec/conformance/run_conformance.sh`.

## Regression fixtures

`tests/fixtures/` holds **17** `T-*.md` regression fixtures (golden, hand-stamped,
inverted-eval variants, envelope-tampering cases) plus `oracle.json` declaring the
expected verdict per fixture. Consumed by `test-task-spec-skill.sh --suite fixtures`.

## What is covered

| Step | Script (under `src/`) | Assertion |
|------|-----------------------|-----------|
| 1 | `author/generate-task-spec.sh` | Creates a file with correct ID ↔ filename match |
| 2 | — | Fills the generated stub with a valid Task-Spec v2 |
| 3 | `gate/validate-task-spec.sh` | Passes on a well-formed task |
| 4 | `gate/validate-task-spec.sh` | Fails with a specific error when a placeholder is injected |
| 5 | `backlog/transition-status.sh` | `ready → in-progress` updates status and keeps file in `tasks/` |
| 6 | `backlog/transition-status.sh` | `in-progress → done` moves file to `tasks/done/` |
| 7 | `backlog/rebuild-state.sh` | Rebuilds `_state.yaml` and reflects the correct status |
| 8 | `backlog/list-ready.sh` | Excludes done tasks from the ready queue |
| 9 | `backlog/archive.sh` | Is a no-op when all done/parked tasks are already archived |
| 10 | `backlog/backup-backlog.sh` | Creates a `.tar.gz` archive in the requested directory |

## Isolation strategy

The scripts operate relative to the current working directory and do not accept a
`--root` override. The self-test therefore:

1. Creates a temp directory (`mktemp -d`).
2. `cd`s into it and runs `git init` so `validate-task-spec.sh` can resolve a
   repository root for path lookups.
3. Calls the engine scripts via absolute paths; their internal repo-root lookup
   (`src/<verb>/` → `../lib/_lib.sh`) still finds templates and sibling scripts
   correctly.
4. Uses `trap 'rm -rf "$TMPDIR"' EXIT` so cleanup happens even on early failure.

## macOS compatibility

`transition-status.sh` uses `flock(1)` (from `util-linux`), which is not present on
macOS. The self-test detects the missing binary and prepends a minimal shim to
`PATH`. The shim is safe because the test environment is single-threaded with no
concurrent access.
