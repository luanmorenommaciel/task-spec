# Task-Spec format v4 — evidence policy

> **Status:** opt-in in engine 3.9.0. Format v3 remains the authoring default;
> formats v1–v4 remain readable. There is no format-v5 change.

Format v4 keeps the v3 atomic task, six zones, bounded write scope, runnable
evals, HMAC authorization, and independent POST-gate. It adds sealed policy for
evidence that cannot safely or honestly live inside the executor prompt.

## Policy fields

```yaml
format_version: 4
evaluation_policy:
  acceptance_scope: portable  # local | portable | human-authorized
  max_age_sec: 86400           # optional; absent means ordering only
  deterministic:
    required: true
  holdout:
    required: true
    descriptor_digest: sha256:<public-descriptor-digest>
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
evidence_refs:
  - ref: .taskspec/evidence/research.json
    digest: sha256:<file-digest>
    role: context  # context | constraint | risk
```

At least one evaluation class must be required. Portable acceptance also
requires an environment contract. Unresolved Open Questions require
`status: blocked`; an executor may not silently decide them.

Authoring evidence is optional and sealed. Its digest must match
`AuthoringEvidence/v1`; `role: acceptance` is forbidden. Research may inform
context, constraints, and risks, but cannot authorize work or satisfy an eval.

## Evaluation classes

| Class | Evidence | Boundary |
|---|---|---|
| deterministic | local Exit Check | rerun directly by acceptance |
| holdout | `EvaluationReceipt/v2` | private command remains evaluator-side |
| graded | `GradedEvaluationReceipt/v2` | rubric digest, score, threshold, result |
| human | `HumanAcceptanceReceipt/v2` | accountable owner and decision |
| environment | `EnvironmentReceipt/v2` | external enforcement observation |

Every v2 receipt uses `ReceiptSubject/v1`, binding task ID, task revision,
HMAC v3 authorization, attempt ID, and base commit. Its observation time must
follow authorization and handoff. Legacy receipt v1 remains readable only as
supervised Tier 2 and cannot use `structural:<task-id>` for required evidence.

For local scope, structurally valid v2 receipts may satisfy policy. Portable
and human-authorized scope require Ed25519-signed external receipts for every
required non-deterministic evidence class. Trusted public keys and allowed
receipt classes live in `.taskspec/trust/evaluators.json` as
`EvaluatorTrust/v1`; private keys remain external.

## Authorization and handoff

All new v3 and v4 tasks use `TaskAuthorization/v3` over `TaskRevision/v1`.
Changing format, policy, environment, evidence links, scope, graph meaning, or
any unknown future field retires the authorization. HMAC v1/v2 remain readable
as authentic-but-narrow Tier 2.

All newly authorized leaves emit `TaskHandoff/v3`, containing public policy,
revision, attempt, Git base, dependency closure, receipt requirements, scope,
budgets, and commands. It excludes credentials, private holdout commands, and
private evaluator instructions. Handoff v1/v2 parsers remain compatible; new
writers use v3.

## Acceptance

Format-v4 Tier-1 acceptance requires:

1. verified HMAC v3 authorization;
2. matching `TaskHandoff/v3`;
3. unchanged dependency closure and non-diverged Git base;
4. passing eval and commit-aware, symlink-safe blast radius;
5. every required receipt matching subject, time, policy, and signer rule;
6. atomic `AcceptanceRecord/v1` plus complete task acceptance envelope.

Missing keys, narrow signatures, legacy receipts, or `--no-blast-radius` force
Tier 2. Tier-2 acceptance requires all of:

```text
--allow-tier2 --supervised-by <identity> --reason <text>
```

Stable machine failures use `AcceptanceFailure/v1`, including policy tamper,
stale handoff, divergent base, closure drift, blast radius, eval failure,
receipt mismatch/staleness/signature, and insufficient tier.

## Environment boundary

`EnvironmentContract/v1` declares runtime, network, filesystem, and resource
expectations. Task-Spec validates and binds the claim; an external sandbox must
actually enforce it and issue the receipt. Checked-in JSON alone is not proof of
isolation.

## Optional interoperability

A2A v1.0, the current MCP bridge, and DSSE receipt export are non-normative
adapters. They must round-trip revision, authorization, scope, budgets, and
evidence requirements. DSSE proves signed bytes and payload type, not semantic
truth or key trust.

## Non-claims

Format v4 provides no model, scheduler, fleet, hosted dispatcher, production
sandbox, semantic oracle, runtime-created dependency, or silent replanner.
Converge and harness skills own interviews, orchestration, runtime binding,
trackers, loops, and fleet concerns.
