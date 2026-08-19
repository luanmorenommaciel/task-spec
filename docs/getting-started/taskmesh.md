# Run authorized work with TaskMesh

TaskMesh is the optional execution control plane included with Task-Spec 3.9.
It does not write tasks, authorize scope, or replace acceptance. It consumes the
ready frontier that Task-Spec already derives, gives each leaf one fenced
attempt, and returns the result to canonical Task-Spec verification.

## Install the optional runtime

From a private release checkout or authenticated source checkout:

```bash
bash install.sh --global --copy --with-mesh
export PATH="$HOME/.local/bin:$PATH"
taskspec mesh doctor
```

The installer selects macOS or Linux and amd64 or arm64, verifies the helper's
SHA-256, and requires its product version to equal `taskspec version`. Without
`--with-mesh`, no daemon or helper is installed.

## Prepare the frontier

TaskMesh will not schedule drafts, blocked dependencies, composition nodes, or
narrow legacy authorization. Create and authorize leaves through Task-Spec:

```bash
taskspec graph --check
taskspec ready
taskspec mesh frontier
taskspec mesh explain --task T-…
```

`frontier` is a runtime view of the canonical `TaskGraphView/v1`. Harnesses and
models are runtime candidates, never graph nodes.

## Name the model (roster)

TaskMesh used to pick an adapter and leave `model` empty. OMP then used
whatever default sat on the Pi. That is a bug. A repository may now declare
ordered candidates by effort, with optional kind overrides:

```json
{
  "contract": "TaskMeshRoster/v1",
  "require_named_model": true,
  "bands": {
    "XS": {
      "candidates": [
        {"adapter": "omp-rpc", "model": "deepseek-v4-flash", "provider": "omp"}
      ]
    },
    "S": {
      "candidates": [
        {"adapter": "grok-native", "model": "grok-4.6"},
        {"adapter": "omp-rpc", "model": "deepseek-v4-pro", "provider": "omp"}
      ]
    },
    "M": {
      "candidates": [
        {"adapter": "codex-native", "model": "gpt-5.6"},
        {"adapter": "claude-native", "model": "claude-opus-5"}
      ]
    },
    "L": {
      "candidates": [
        {"adapter": "claude-native", "model": "claude-opus-5"},
        {"adapter": "codex-native", "model": "gpt-5.6"}
      ]
    }
  },
  "kinds": {
    "design": {"prefer": ["claude-native", "grok-native"]},
    "mechanical": {"prefer": ["omp-rpc", "grok-native"]},
    "git": {"prefer": ["codex-native"]}
  }
}
```

Write that file as `tasks/.mesh/roster.json`. `taskspec mesh explain --task T-…`
prints the selected `route.model`. `--model` on the CLI still wins. A roster
with `require_named_model: true` refuses an empty model instead of calling OMP
with a blank. Kind is read from the task's `kind:` field or from a `tags:`
value of `design`, `mechanical`, or `git`. Roster mode is a preference among
adapters; it does not silently promote a supervised run to autonomous.

## Run one supervised leaf

```bash
taskspec mesh run --task T-… --adapter claude-native --execute
taskspec mesh watch <run-id>
taskspec mesh status <attempt-id>
```

The daemon creates a run branch, an attempt branch, and a TaskMesh-owned Git
worktree. The adapter receives one `TaskHandoff/v3`; author and evaluator keys
are never forwarded. When execution reaches `awaiting_supervision`, inspect the
patch and evidence, then explicitly accept or park it:

```bash
taskspec mesh accept <attempt-id> \
  --supervised-by <identity> \
  --reason "reviewed the bounded patch and acceptance evidence"
```

A supervised worktree is process separation, not a security sandbox. The
acceptance receipt records that limitation.

## Move between cockpits

The daemon owns the durable run, not the shell that started it. Codex can start
a run, Claude can reconnect to `status` or `watch`, and Grok can use the local
MCP facade. Every cockpit sees the same ordered event history and fenced lease:

```bash
taskspec mesh mcp
taskspec mesh watch <run-id> --after <sequence>
```

The MCP facade is stateless and local. It exposes frontier, route explanation,
start, observe, cancel, supervised accept, and finish; it cannot bypass
Task-Spec authorization or acceptance.

## Autonomous OMP execution

Autonomous mode is deliberately narrower. It requires Docker or Podman, the
pinned OMP worker image, an external credential gateway, and host-side Ed25519
attestation keys:

```bash
taskspec mesh setup sandbox
taskspec mesh run --task T-… --mode autonomous \
  --provider <provider> --model <model> --execute
```

The worker runs non-root with a read-only root filesystem, one writable
workspace, bounded resources, dropped capabilities, `no-new-privileges`, and a
short-lived attempt capability. Provider credentials remain in the host proxy.
If TaskMesh cannot prove that boundary, autonomous execution fails; it never
falls back to supervised mode silently.

## Finish safely

Accepted, conflict-free attempt branches are merged only into the run's
integration branch. When every run task is integrated:

```bash
taskspec mesh finish <run-id>
```

`finish` prints the exact human merge route. It does not check out, merge,
push, or open a pull request against the target branch.

Read [TaskMesh contracts](../reference/taskmesh-contracts.md) for the typed API
and [TaskMesh trust boundaries](../trust/taskmesh-boundaries.md) before enabling
autonomous execution.
