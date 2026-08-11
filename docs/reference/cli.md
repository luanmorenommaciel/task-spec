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

Stable machine tokens include `INIT=OK`, `TASK_PLAN=OK`, `TASK_BATCH=OK`,
`DOD=COMPLETE`, `TIER=1|2`, `ACCEPTED=0|1`, and `INSTALL=OK`. A token is not a
substitute for the associated report or JSON contract.
