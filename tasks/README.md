# tasks/ — this repository's backlog

These files are **Task-Spec's own dogfooded work**, not the public tutorial.

| Look here | For |
|---|---|
| [docs/examples/](../docs/examples/README.md) | Worked TaskPlan, composition, evidence, and handoff shapes |
| `T-*.md` in this directory | Live engine chores: the user-authorized native toolkit implementation |
| `done/` | Frozen accepted history. Do not rewrite it to match a later tree |
| `parked/` | Non-executable composition nodes whose children already shipped |
| `.taskspec/acceptance/` | Matching acceptance receipts. Also frozen |
| `.plans/` | Historical release manifests and the reviewed toolkit implementation plan |

A first clone should learn the format from `docs/examples/` and
`spec/task-spec-v3.md`, not from this directory.

`parked/T-20260815-release-381.md` and `parked/T-20260816-taskmesh-390.md`
are XXL composition nodes. Every child is in `done/`; 3.8.1 and 3.9.0 already
shipped. The nodes themselves are not executable (`execution_backend: none`).

`_state.yaml` and `_metrics.jsonl` are regenerated locally and are gitignored.

The toolkit CI leaf provisions the private decomposition runtime before the release gate on Linux and macOS. Hosted results remain distinct from local checks.
