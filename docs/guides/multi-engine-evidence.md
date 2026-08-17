# Multi-engine evidence

The engine matrix turns “works with many models” into a reproducible experiment
without fabricating unavailable runs.

1. Freeze a sealed handoff, source commit, fixtures, environment contract, and
   acceptance policy.
2. Record exactly one entry for each family: OpenAI, Anthropic, Google, xAI,
   DeepSeek, Kimi, MiniMax, Qwen, and GLM.
3. Pin provider, model ID, adapter version, and argv. Keep credentials outside
   the matrix.
4. Preview with `taskspec evidence plan`.
5. Run enabled entries into a fresh output directory. Each enabled adapter gets
   a detached Git worktree at the frozen source commit plus the sealed spec
   overlay; its command may use `{handoff}`, `{workspace}`, `{spec}`, and
   `{output}` placeholders. The worktree is removed after status and patch
   evidence is retained.
6. Optionally declare `acceptance_argv` for an independent POST check. Its exit
   code becomes `accepted` or `rejected`; absence remains `not_run`.
7. Retain raw outputs and typed `EngineRunReceipt/v1` files. Mark missing credentials or runners as
   `unavailable`, never as pass.
8. Compare terminal outcome, acceptance verdict, attempts, artifacts,
   deviations, and environment—not writing style.

```bash
taskspec evidence validate release/3.7/engine-matrix.json
taskspec evidence plan release/3.7/engine-matrix.json \
  --handoff release/3.7/task-handoff.json --out-dir release/3.7/runs
taskspec evidence run release/3.7/engine-matrix.json \
  --handoff release/3.7/task-handoff.json --out-dir release/3.7/runs
```

The checked-in release matrix is a template with disabled entries. It validates
the nine-family experimental surface but makes no real-engine result claim.
Published evidence must include the generated receipts and the source commit.
