# Evidence receipts

A receipt is a typed statement about one bounded event. It is not a transcript,
a provider credential, or a universal correctness claim.

Task-Spec 3.7 defines:

- `EvaluationReceipt/v1` for deterministic or hidden-holdout results;
- `GradedEvaluationReceipt/v1` for a score, threshold, rubric digest, and result;
- `HumanAcceptanceReceipt/v1` for an accountable owner decision;
- `EnvironmentReceipt/v1` for enforcement of a declared environment digest;
- `AuthorizationReceipt/v1` for optional Ed25519 signer attribution;
- `EngineRunReceipt/v1` for exact provider, model, adapter, source, environment,
  attempts, outcome, acceptance, artifacts, and deviations.

Every policy receipt binds to the task ID. Graded and human receipts also bind
to the HMAC authorization reference, so changing the sealed contract makes old
receipts unusable. Receipt validation rejects credential-bearing key names;
secrets remain external.

```bash
taskspec receipt validate evidence/*.json
taskspec accept --stamp \
  --holdout-receipt evidence/holdout.json \
  --graded-receipt evidence/graded.json \
  --human-receipt evidence/human.json \
  --environment-receipt evidence/environment.json \
  tasks/T-….md
```

Receipts support comparison without flattening differences. Two engines may
both pass while using different attempts, environments, or deviations. Keep
those facts visible in an evidence matrix instead of converting them into a
single marketing score.
