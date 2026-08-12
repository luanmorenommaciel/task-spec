# Task-Spec format v4 — evidence, integrity, and portability

> **Status:** opt-in in engine 3.7.0. Format v3 remains stable and is not
> migrated automatically.

Format v4 keeps the atomic task, six zones, bounded write scope, runnable evals,
HMAC authorization, and independent POST gate from v3. It adds an explicit
policy for evidence that cannot safely live inside the executor's prompt.

## The policy boundary

```yaml
format_version: 4
evaluation_policy:
  acceptance_scope: portable  # local | portable | human-authorized
  deterministic:
    required: true
  holdout:
    required: true
    authorization_ref: sha256:<bundle-digest>
  graded:
    required: true
    rubric_digest: sha256:<rubric-digest>
    threshold: 0.8
  human:
    required: true
    owner: release-owner
environment_contract:
  required: true
  ref: evidence/environment.json
  digest: sha256:<canonical-contract-digest>
identity_policy:
  required: false
```

At least one evaluation class must be required. A `portable` acceptance scope
also requires an environment contract. An unresolved `## Open Questions`
section requires `status: blocked`; the executor cannot turn a semantic fork
into a silent assumption.

## Four evaluation classes

| Class | Runs where | Receipt | Trust contribution |
|---|---|---|---|
| deterministic | task workspace | local gate output | repeatable behavioral proof |
| holdout | evaluator-controlled workspace | `EvaluationReceipt/v1` | checks hidden from the executor |
| graded | independent rubric evaluator | `GradedEvaluationReceipt/v1` | bounded judgment with threshold and rubric digest |
| human | accountable owner | `HumanAcceptanceReceipt/v1` | explicit semantic or risk acceptance |

`holdout` is not a `check_type` in the public Validation Card because putting
its implementation there would reveal it. The Task-Spec carries only the
commitment; the private bundle stays outside `TaskHandoff/v2`.

## Authorization and identity

HMAC v2 remains the repository authorization seal and the compatibility path
for every v3/v4 task. It proves that the body and authority fields have not
changed under the repository key. It does not identify one human.

When stronger attribution is needed, `AuthorizationReceipt/v1` signs the task
ID and HMAC authorization reference with Ed25519. Revocation is an explicit
registry check. Identity is optional and layered—it does not replace HMAC,
sandboxing, or accountable review.

## Environment evidence

`EnvironmentContract/v1` declares runtime, network, filesystem, and optional
resource limits. `EnvironmentReceipt/v1` records that a named provider enforced
the canonical contract digest. A receipt is evidence from that provider; the
Task-Spec CLI does not claim it created a secure sandbox merely because JSON
exists.

## Acceptance

`taskspec accept` always runs the existing deterministic, blast-radius, and
HMAC gates. For v4 it adds Gate F and requires every receipt marked `required`
by the policy. Task ID, authorization reference, rubric, threshold, owner,
environment digest, and trusted identity must match. Missing or failed evidence
blocks acceptance.

Format v3 follows the exact historical path and requires no v4 receipts.

## Portability

`TaskHandoff/v2` is emitted only for format v4. It contains the public policy,
environment commitment, identity requirement, and receipt contract names. It
never contains private holdout commands, signing keys, API credentials, or
provider secrets. A2A and MCP bridges embed this same handoff and verify that
task ID and spec digest survive the round trip.

The multi-engine harness refuses an enabled run if the handoff digest is stale,
creates one detached Git worktree per engine at the recorded source commit, and
retains output, status, patch, and `EngineRunReceipt/v1` evidence before cleanup.

## Non-claims

Format v4 does not provide a model, scheduler, fleet manager, production
sandbox, accounting policy, deployment proof, or semantic oracle. A passing
receipt proves the named check under the named environment and authorization;
it does not prove all possible correctness.
