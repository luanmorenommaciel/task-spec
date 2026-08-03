# task-spec GitHub Action — the CI eval-gate

This composite action is the **referee of record** for task-spec backlogs. An
agent can paste a green checkmark into a PR description; it cannot paste one
into CI. Once this action is wired, the merge gate stops trusting agent-pasted
GREEN and trusts only what the evals themselves return on the runner.

## What it does

1. Installs the `taskspec` CLI from this repo (`engine-ref` input, default `main`).
2. `taskspec validate --skip-touches-paths` on every file matching `tasks-glob`
   (structural lint — the PRE-gate shape; touches_paths is skipped because CI
   checks out a sparse diff view).
3. With `mode: run`, additionally `taskspec run --ci` on each file — one JSON
   object per eval on stdout.
4. **Fails the build on any non-zero exit.** No envelope stamping happens in CI
   (`--stamp` is an author-side act); this gate is read-only.

## Usage

```yaml
# .github/workflows/taskspec-gate.yml
name: taskspec eval gate
on: [push, pull_request]
jobs:
  eval-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: luanmorenommaciel/task-spec/integrations/github-action@main
        with:
          tasks-glob: "tasks/T-*.md"
          mode: run            # validate | run
```

## Honest limits

- `mode: validate` proves structure, not outcomes. `mode: run` proves the evals
  execute — a green run on unbuilt work means the evals themselves are weak, not
  that the work is done. The full is-the-work-real check is
  `taskspec accept --gold-sanity` against the merged result, which needs the
  baseline ref available (fetch-depth: 0) and is deliberately NOT this action's
  default.
- The eval runner needs a git repo (it resolves `git rev-parse`); the action
  assumes the checkout step ran first.
