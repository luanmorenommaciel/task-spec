# TaskMesh trust boundaries

TaskMesh is an execution control plane, not a new authorization system. Its
strongest invariant is that runtime convenience cannot widen a signed
Task-Spec leaf.

## What each layer proves

| Mechanism | Proves | Does not prove |
|---|---|---|
| Canonical ready frontier | the leaf is authorized and dependency-ready in the observed graph | that a chosen model will perform well |
| Dispatch decision | every candidate passed deterministic eligibility and the selected route is explainable | model correctness or semantic judgment |
| Lease and fence | only the current attempt may remain authoritative | exactly-once provider execution |
| Supervised worktree | bounded Git branch/worktree ownership and inspectable changes | hostile-code isolation |
| Autonomous container | the recorded container, mount, resource, network, and credential boundary was observed | universal host security or evaluator wisdom |
| Signed sandbox evidence | bytes came from a trusted evaluator key for this receipt class | that JSON alone creates enforcement |
| Canonical acceptance | Task-Spec gates passed for the exact revision, attempt, base, scope, and required evidence | deployment or production reliability |
| Integration branch | accepted attempts compose without mutating the target | that a human should merge the branch |

## Credential boundary

TaskMesh never stores provider/model credentials in its database, handoff,
event stream, artifacts, or Task-Spec files. In autonomous OMP mode:

1. The host issues an expiring attempt token.
2. The worker receives only that token through a read-only capability file.
3. A host-side proxy validates attempt, expiry, provider, model, and route.
4. The proxy substitutes the upstream capability outside the worker.
5. Completion revokes the lease and removes capability files.

Known secret patterns are redacted before bounded process output is persisted.
Task-Spec signing keys, evaluator keys, private holdouts, SSH agents, home
directories, and container sockets never enter the worker.

## Supervised versus autonomous

| Mode | Initial adapters | Isolation claim | Acceptance |
|---|---|---|---|
| Supervised | Codex, Claude Code, Grok Build, OMP | TaskMesh-owned Git worktree only | waits for explicit supervisor identity and reason |
| Autonomous | OMP in the pinned worker | externally attested container and credential boundary | requires valid attempt-bound environment evidence |

There is no silent downgrade. If the image, runtime, proxy, credential lease,
or attestor cannot be verified, autonomous mode fails with a stable code.

## Operational boundaries

TaskMesh does not decompose tasks, invent dependencies, rewrite a signed leaf,
run OMP subagent fan-out, merge the target branch, push Git state, create pull
requests, or provide a hosted control plane. Converge remains the higher-level
intent, planning, tracker, and assurance workflow; TaskMesh is the optional
portable execution layer underneath it.

The 3.9 conformance corridor demonstrates bounded synthetic executions,
recovery, isolation, and cross-cockpit continuity. It is not a claim of
long-running production reliability or ecosystem certification.
