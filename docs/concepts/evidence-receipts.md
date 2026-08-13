# Evidence receipts

A receipt is a typed statement about one bounded observation. It is not a
transcript, credential, authorization, or universal correctness claim.

New evidence writers emit v2 receipts with `ReceiptSubject/v1`:

```yaml
subject:
  task_id: T-…
  task_revision_digest: sha256:…
  authorization_ref: hmac-sha256-v3:…
  attempt_id: 00000000-0000-4000-8000-000000000000
  base_commit: <full Git SHA>
observed_at: <UTC timestamp>
```

The subject prevents reuse across tasks, revisions, authorizations, attempts,
and Git bases. Receipt time must be at or after authorization and handoff;
sealed v4 policy may also set `max_age_sec`.

| Receipt | Represents |
|---|---|
| `EvaluationReceipt/v2` | deterministic or private-holdout result |
| `GradedEvaluationReceipt/v2` | rubric digest, score, threshold, and result |
| `HumanAcceptanceReceipt/v2` | accountable human decision |
| `EnvironmentReceipt/v2` | an external enforcer's observation of a declared environment |
| `EngineRunReceipt/v2` | provider/model/adapter attempt and retained artifacts |
| `AuthorizationReceipt/v1` | optional Ed25519 attribution of repository authorization |

Legacy v1 receipts remain parseable but count only as Tier-2 evidence. A
required receipt may not use `structural:<task-id>` as an authorization
fallback.

For `local` policy, structurally valid v2 receipts are sufficient. For
`portable` and `human-authorized` policy, every non-deterministic required v2
receipt must carry an Ed25519 signature from a key authorized for that receipt
class in `.taskspec/trust/evaluators.json` (`EvaluatorTrust/v1`). Private keys
stay outside the repository and executor environment.

```bash
taskspec receipt sign evidence/holdout.json \
  --private-key /secure/evaluator.pem \
  --public-key .taskspec/trust/evaluator.pub.pem \
  --out evidence/holdout-signed.json

taskspec accept --stamp \
  --handoff .taskspec/handoffs/attempt.json \
  --trust-registry .taskspec/trust/evaluators.json \
  --holdout-receipt evidence/holdout-signed.json \
  tasks/T-….md
```

DSSE/in-toto-style export is optional:

```bash
taskspec dsse export evidence/holdout-signed.json \
  --private-key /secure/evaluator.pem \
  --public-key .taskspec/trust/evaluator.pub.pem \
  --out evidence/holdout.dsse.json
taskspec dsse verify evidence/holdout.dsse.json \
  --public-key .taskspec/trust/evaluator.pub.pem
```

DSSE proves signed bytes and payload type. It does not prove semantic truth or
that a key should be trusted.
