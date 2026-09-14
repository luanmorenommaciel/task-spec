# CLI reference

Generated from `src/cli/commands.json`. Global `--json` emits TaskSpecCLIResult/v1.

## init

```text
Usage: taskspec init [--force]
```

creates missing tasks/ and .taskspec/config

## setup

```text
Usage: taskspec setup | taskspec setup signing [--force] | taskspec setup decompose
```

none

## setup signing

```text
Usage: taskspec setup signing
```

creates or explicitly rotates the repository-private HMAC key

## demo

```text
Usage: taskspec demo
```

creates and removes an isolated temporary repository

## example

```text
Usage: taskspec example task-plan --out <file> [--force]
```

writes one installed canonical example non-clobberingly; --force replaces and --dry-run writes nothing
Examples: task-plan, intent, recipe, incident, release-evidence. Use taskspec help example <kind>.

## new

```text
Usage: taskspec new [--format 3|4] [--status ready|blocked] [--queue] <slug> <XS|S|M|L|XL|XXL> [agent] [source-note]
```

creates one Task-Spec scaffold and derived state

## plan

```text
Usage: taskspec plan --manifest <TaskPlan.yaml>
```

none

## batch

```text
Usage: taskspec batch --plan <TaskPlan.yaml> | taskspec batch --intent-file <file> --effort <size>
```

creates declared Task-Spec scaffolds; --dry-run writes nothing

## migrate

```text
Usage: taskspec migrate <task-spec>
```

atomically upgrades one explicitly named legacy task under the task-state lock

## validate

```text
Usage: taskspec validate [--no-state] <task-spec>
```

refreshes deterministic derived state unless --no-state

## dod

```text
Usage: taskspec dod <task-spec>
```

none

## gate

```text
Usage: taskspec gate [--stamp] [--require-tier1] <task-spec>
```

executes task evals; --stamp additionally writes the sign-off envelope

## handoff

```text
Usage: taskspec handoff <task-spec> --backend <token> [--out <file>] [--attempt-id <uuid>]
```

stdout is read-only; --out writes non-clobberingly unless --force

## run

```text
Usage: taskspec run [--ci] <task-spec>
```

runs declared eval commands in the task workspace

## accept

```text
Usage: taskspec accept [--stamp] [--handoff <file>] [receipt flags] <task-spec>
```

executes acceptance evals; --stamp additionally writes AcceptanceRecord/v1 and the acceptance envelope

## author-doctor

```text
Usage: taskspec author-doctor <task-spec>
```

none

## holdout

```text
Usage: taskspec holdout seal|verify|run ...
```

seal/run may write descriptor or receipt; verify is read-only

## receipt

```text
Usage: taskspec receipt validate|sign|engine|environment|evaluation|graded|human ...
```

creator/sign commands write explicit receipt paths; validate is read-only

## eval-audit

```text
Usage: taskspec eval-audit <task-spec> --baseline <git-ref> [--mutations <matrix>] [--repeat N]
```

uses temporary git worktrees; optional report path

## identity

```text
Usage: taskspec identity init|sign|verify|revoke ...
```

init/sign/revoke write explicit files; verify is read-only

## evidence

```text
Usage: taskspec evidence validate|plan|run <EngineMatrix.json> ...
```

run writes an explicit evidence directory; validate/plan are read-only

## bridge

```text
Usage: taskspec bridge export|validate ...
```

export writes only with --out; validate is read-only

## dsse

```text
Usage: taskspec dsse export|verify ...
```

export writes only to --out; verify is read-only

## mcp

```text
Usage: taskspec mcp
```

read-only stdio server

## mesh

```text
Usage: taskspec mesh <init|doctor|serve|frontier|run|status|watch|explain|cancel|resume|accept|finish|adapters|setup|mcp> ... | taskspec mesh run --initiative <id> [--execute]
```

optional repository-local control plane; run/cancel/resume/accept/finish/setup mutate disposable mesh state while canonical acceptance still calls Task-Spec

## ready

```text
Usage: taskspec ready [--all] [filters]
```

none

## graph

```text
Usage: taskspec graph [--task <id>] [--check] [--mermaid] [--json] | taskspec graph --initiative <id> --view tasks|capabilities
```

none; TaskGraphView/v1 is derived from Markdown and Git

## status

```text
Usage: taskspec status <task-id-or-path> [--json] | taskspec status --initiative <id>
```

none; emits TaskStatus/v1 and exactly one safe next command

## lint

```text
Usage: taskspec lint
```

none

## transition

```text
Usage: taskspec transition <task-id> <ready|in-progress|blocked|done|parked> [reason]
```

changes lifecycle status and derived state

## rebuild-state

```text
Usage: taskspec rebuild-state
```

rewrites deterministic tasks/_state.yaml

## archive

```text
Usage: taskspec archive
```

moves root done/parked tasks under the task-state lock and refreshes derived state

## backup

```text
Usage: taskspec backup [destination-directory]
```

writes a timestamped backlog archive to the selected destination

## metrics

```text
Usage: taskspec metrics [--since YYYY-MM-DD] [--author <name>] [--status <status>]
```

none

## conformance

```text
Usage: taskspec conformance --self-test | --level L0|L1|L2 --executor <command>
```

self-test uses disposable fixtures only

## executor

```text
Usage: taskspec executor <task-spec>
```

reference L2 executor; transitions, executes, accepts, or parks one supplied task

## agent-context

```text
Usage: taskspec agent-context
```

none

## completion

```text
Usage: taskspec completion bash|zsh|fish
```

none

## doctor

```text
Usage: taskspec doctor [--backlog]
```

none

## version

```text
Usage: taskspec version
```

none

## help

```text
Usage: taskspec help [command]
```

none

## decompose

```text
Usage: taskspec decompose init|prepare|review|compile|status|impact|import <initiative> [options]
```

Native intent decomposition, signed topology review, and TaskPlan compilation.

## recipe

```text
Usage: taskspec recipe list|show <strategy>|validate <file> [--budget <n>]
```

Inspect and validate resolved bounded execution guidance.

## guide

```text
Usage: taskspec guide <topic>
```

Read version-matched installed workflow guidance.

## decompose init

```text
Usage: taskspec decompose init <initiative> --intent-file <file|->
```

Create explicit intent workspace.

## decompose prepare

```text
Usage: taskspec decompose prepare <initiative> --recipe <file> [--replace]
```

Validate and project an authored recipe; never approve it.

## decompose review

```text
Usage: taskspec decompose review <initiative> --accept --reviewer <name> --reason <text>
```

Authenticate explicit approval of the current topology.

## decompose compile

```text
Usage: taskspec decompose compile <initiative>
```

Compile reviewed topology and lineage without sealing leaves.

## decompose status

```text
Usage: taskspec decompose status <initiative>
```

Explain planning blockers and next valid action.

## decompose impact

```text
Usage: taskspec decompose impact <initiative> --against <bundle-or-snapshot.json>
```

Compare leaf projections to identify affected authorizations.

## decompose import

```text
Usage: taskspec decompose import <initiative> --source <workspace>
```

Explicitly import originals; fresh native review required.

## recipe list

```text
Usage: taskspec recipe list 
```

List available pinned strategies.

## recipe show

```text
Usage: taskspec recipe show <strategy>
```

Show resolved guidance.

## recipe validate

```text
Usage: taskspec recipe validate <file> [--budget <n>]
```

Validate a resolved recipe.

## setup decompose

```text
Usage: taskspec setup decompose 
```

Provision locked dependencies in the private runtime.

## receipt operational

```text
Usage: taskspec receipt operational validate <file> | import <file> --out <path>
```

Validate or import operational evidence without upgrading its trust.

## mesh init

```text
Usage: taskspec mesh init 
```

Use the existing TaskMesh init operation.

## mesh doctor

```text
Usage: taskspec mesh doctor 
```

Use the existing TaskMesh doctor operation.

## mesh serve

```text
Usage: taskspec mesh serve --foreground
```

Use the existing TaskMesh serve operation.

## mesh frontier

```text
Usage: taskspec mesh frontier 
```

Use the existing TaskMesh frontier operation.

## mesh run

```text
Usage: taskspec mesh run --task <id>|--frontier|--initiative <id> [--adapter <name>] [--model <id>] [--provider <id>] [--mode supervised|autonomous] [--max-parallel <n>] [--execute]
```

Creates a run, worktree and lease; --execute starts the executor; --dry-run previews without creating them.

## mesh status

```text
Usage: taskspec mesh status [<run-or-attempt>]
```

Use the existing TaskMesh status operation.

## mesh watch

```text
Usage: taskspec mesh watch <run> [--after <sequence>]
```

Use the existing TaskMesh watch operation.

## mesh explain

```text
Usage: taskspec mesh explain --task <id> [--adapter <name>] [--model <id>]
```

Use the existing TaskMesh explain operation.

## mesh cancel

```text
Usage: taskspec mesh cancel <attempt>
```

Use the existing TaskMesh cancel operation.

## mesh resume

```text
Usage: taskspec mesh resume <run-or-attempt> [--execute]
```

Use the existing TaskMesh resume operation.

## mesh accept

```text
Usage: taskspec mesh accept <attempt> --supervised-by <identity> --reason <text>
```

Use the existing TaskMesh accept operation.

## mesh finish

```text
Usage: taskspec mesh finish <run>
```

Use the existing TaskMesh finish operation.

## mesh adapters

```text
Usage: taskspec mesh adapters list|probe [<name>]
```

Use the existing TaskMesh adapters operation.

## mesh setup

```text
Usage: taskspec mesh setup sandbox
```

Use the existing TaskMesh setup operation.

## mesh mcp

```text
Usage: taskspec mesh mcp 
```

Use the existing TaskMesh mcp operation.

## example task-plan

```text
Usage: taskspec example task-plan --out <file> [--force]
```

Write the installed task-plan example; existing output requires explicit --force.

## example intent

```text
Usage: taskspec example intent --out <file> [--force]
```

Write the installed intent example; existing output requires explicit --force.

## example recipe

```text
Usage: taskspec example recipe --out <file> [--force]
```

Write the installed recipe example; existing output requires explicit --force.

## example incident

```text
Usage: taskspec example incident --out <file> [--force]
```

Write the installed incident example; existing output requires explicit --force.

## example release-evidence

```text
Usage: taskspec example release-evidence --out <file> [--force]
```

Write the installed release-evidence example; existing output requires explicit --force.

