# CLI reference

The default surface is human-readable. Global `--json` wraps command output in
`TaskSpecCLIResult/v1` while preserving the underlying exit code. Global
`--dry-run` prevents supported mutations.

| Exit | Meaning |
|---:|---|
| 0 | Success or positive proof |
| 1 | Invalid contract, failed eval, rejected gate, or rejected acceptance |
| 2 | Usage error |
| 3 | Unsupported runtime floor, such as a Bash-4-only auxiliary script |

```bash
taskspec help
taskspec agent-context
taskspec completion bash
taskspec completion zsh
taskspec completion fish
```

Stable machine tokens include `INIT=OK`, `DEMO=READY`, `TASK_PLAN=OK`, `TASK_BATCH=OK`,
`DOD=COMPLETE`, `TIER=1|2`, `ACCEPTED=0|1`, and `INSTALL=OK`. A token is not a
substitute for the associated report or JSON contract.

## Installation proof

| Command | Purpose |
|---|---|
| `doctor` | Inspect runtime prerequisites and signing readiness |
| `demo` | Run plan → generate → gate → handoff → eval → accept in a disposable repository |
| `conformance --self-test` | Prove the bundled executor reaches conformance L2 |

## Evidence and interoperability

| Command | Purpose |
|---|---|
| `author-doctor <spec>` | Explain vague goals, weak evals, broad scope, and unresolved decisions |
| `holdout seal|verify|run` | Commit to private evaluator checks and emit a result receipt |
| `receipt validate|engine|environment|graded|human` | Create or validate typed evidence |
| `eval-audit <spec> --baseline <ref>` | Require pass now and failure on baseline/mutations |
| `identity init|sign|verify|revoke` | Optional Ed25519 identity above HMAC v2 |
| `evidence validate|plan|run` | Reproducible nine-family engine experiment |
| `bridge export|validate` | Translate a handoff into A2A/MCP envelopes |
| `mcp` | Start the read-only Task-Spec stdio tool server |
