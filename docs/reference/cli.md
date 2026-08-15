# CLI reference

The default surface is human-readable. Global `--json` wraps command output in
`TaskSpecCLIResult/v1` while preserving the underlying exit code. Plan preview
returns `TaskPlan/v1` in `data`; approved batch materialization returns
`TaskMaterializationReceipt/v1` with generated paths and content hashes while
explicitly recording whether bytes were `created`, `unchanged`, or only
previewed with `dry_run`; no materialization receipt grants dispatch authority. Global
`--dry-run` prevents supported mutations.

On successful `taskspec --json accept --stamp`, `data` is
`AcceptanceFinalized/v1`. It binds the accepted task and attempt to the exact
`AcceptanceRecord/v1` path and `sha256:` digest. Automation consumes that
structured result rather than parsing the human gate transcript.

| Exit | Meaning |
|---:|---|
| 0 | Success or positive proof |
| 1 | Invalid contract, failed eval, rejected gate, or rejected acceptance |
| 2 | Usage error |
| 3 | Unsupported runtime floor, such as a Bash-4-only auxiliary script |

```bash
taskspec help
taskspec help <command>
taskspec agent-context
taskspec completion bash
taskspec completion zsh
taskspec completion fish
```

Stable machine tokens include `INIT=OK`, `DEMO=READY`, `TASK_PLAN=OK`, `TASK_BATCH=OK`,
`DOD=COMPLETE`, `TIER=1|2`, `ACCEPTED=0|1`, and `INSTALL=OK`. A token is not a
substitute for the associated report or JSON contract.

## Generated command contract

This table is generated from `taskspec agent-context`; documentation lint fails
if the machine contract and reference diverge.

<!-- agent-context:start -->
| Command | Mutation contract | Stable tokens |
|---|---|---|
| `taskspec init` | creates missing tasks/ and .taskspec/config | `INIT=OK`, `INIT=DRY_RUN` |
| `taskspec setup` | none | `SETUP=READY` |
| `taskspec setup signing` | creates or explicitly rotates the repository-private HMAC key | — |
| `taskspec demo` | creates and removes an isolated temporary repository | `DEMO=READY`, `DEMO=DRY_RUN` |
| `taskspec new` | creates one Task-Spec scaffold and derived state | — |
| `taskspec plan` | none | `TASK_PLAN=OK`, `TASK_PLAN=INVALID` |
| `taskspec batch` | creates declared Task-Spec scaffolds; --dry-run writes nothing | `TASK_BATCH=OK`, `TASK_BATCH=DRY_RUN`, `TASK_BATCH=REFUSED` |
| `taskspec migrate` | atomically upgrades one explicitly named legacy task under the task-state lock | — |
| `taskspec validate` | refreshes deterministic derived state unless --no-state | — |
| `taskspec dod` | none | `DOD=COMPLETE`, `DOD=GAPS` |
| `taskspec gate` | --stamp writes the sign-off envelope; otherwise none | `TIER=1`, `TIER=2` |
| `taskspec handoff` | stdout is read-only; --out writes non-clobberingly unless --force | `HANDOFF=WRITTEN`, `HANDOFF=INVALID`, `HANDOFF=REFUSED` |
| `taskspec run` | runs declared eval commands in the task workspace | — |
| `taskspec accept` | --stamp atomically writes AcceptanceRecord/v1 plus the complete acceptance envelope | `ACCEPTED=1`, `ACCEPTED=0`, `ACCEPTANCE_FAILURE=<code>` |
| `taskspec author-doctor` | none | `AUTHOR_DOCTOR=READY`, `AUTHOR_DOCTOR=INVALID` |
| `taskspec holdout` | seal/run may write descriptor or receipt; verify is read-only | `HOLDOUT=SEALED`, `HOLDOUT=VERIFIED`, `HOLDOUT=INVALID` |
| `taskspec receipt` | creator/sign commands write explicit receipt paths; validate is read-only | `RECEIPT=WRITTEN`, `RECEIPT=SIGNED`, `RECEIPT=INVALID` |
| `taskspec eval-audit` | uses temporary git worktrees; optional report path | `EVAL_AUDIT=INVALID` |
| `taskspec identity` | init/sign/revoke write explicit files; verify is read-only | `IDENTITY=READY`, `IDENTITY=SIGNED`, `IDENTITY=VERIFIED`, `IDENTITY=REVOKED` |
| `taskspec evidence` | run writes an explicit evidence directory; validate/plan are read-only | `ENGINE_MATRIX=VALID`, `ENGINE_MATRIX=INVALID` |
| `taskspec bridge` | export writes only with --out; validate is read-only | `BRIDGE=VALID`, `BRIDGE=INVALID` |
| `taskspec dsse` | export writes only to --out; verify is read-only | `DSSE=EXPORTED`, `DSSE=VERIFIED`, `DSSE=INVALID` |
| `taskspec mcp` | read-only stdio server | — |
| `taskspec ready` | none | — |
| `taskspec graph` | none; TaskGraphView/v1 is derived from Markdown and Git | `GRAPH=<digest>`, `GRAPH=INVALID` |
| `taskspec status` | none; emits TaskStatus/v1 and exactly one safe next command | `NEXT=<command>`, `STATUS=INVALID` |
| `taskspec lint` | none | — |
| `taskspec transition` | changes lifecycle status and derived state | — |
| `taskspec rebuild-state` | rewrites deterministic tasks/_state.yaml | — |
| `taskspec archive` | moves root done/parked tasks under the task-state lock and refreshes derived state | — |
| `taskspec backup` | writes a timestamped backlog archive to the selected destination | — |
| `taskspec metrics` | none | — |
| `taskspec conformance` | self-test uses disposable fixtures only | — |
| `taskspec executor` | reference L2 executor; transitions, executes, accepts, or parks one supplied task | — |
| `taskspec agent-context` | none | — |
| `taskspec completion` | none | — |
| `taskspec doctor` | none | `BACKLOG_DOCTOR=READY`, `BACKLOG_DOCTOR=BLOCKED` |
| `taskspec version` | none | — |
| `taskspec help` | none | — |
<!-- agent-context:end -->

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
| `eval-audit ... --repeat N` | Detect mixed repeated outcomes instead of hiding flakes |
| `receipt sign` | Sign a v2 evaluator receipt with Ed25519 |
| `identity init|sign|verify|revoke` | Optional Ed25519 attribution above HMAC v3 |
| `evidence validate|plan|run` | Reproducible nine-family engine experiment |
| `bridge export|validate` | Translate a handoff into optional A2A v1.0/MCP envelopes |
| `dsse export|verify` | Optional DSSE export and independent signature verification for v2 receipts |
| `mcp` | Start the read-only Task-Spec stdio tool server |

## Graph, status, and recovery

| Command | Purpose |
|---|---|
| `graph [--task ID] [--check] [--mermaid] [--json]` | Derive `TaskGraphView/v1`; never write or schedule |
| `status <id-or-path> [--json]` | Emit `TaskStatus/v1` and exactly one safe next command |
| `doctor --backlog` | Audit graph, narrow seals, stale temporaries, acceptance records, and metrics projection |
| `ready [--all]` | Show dependency-unblocked leaves from the shared graph resolver |
