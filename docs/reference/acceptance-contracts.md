# Handoff, receipt, and acceptance contracts

## TaskHandoff/v3

Every new handoff is attempt-bound, regardless of Task-Spec format. It carries:

- task and spec digests plus `TaskRevision/v1`;
- HMAC v3 authorization reference and tier;
- UUID attempt and issue time;
- absolute workspace and immutable Git base commit;
- dependency-closure members and digest;
- write scope, budgets, backend, agent contract, eval and acceptance commands;
- public evidence policy and receipt class requirements.

It contains no credential, evaluator private instruction, or private holdout
command and never starts a model.

```bash
taskspec handoff tasks/T-…-leaf.md --backend codex \
  --out .taskspec/handoffs/attempt.json
```

`--out` refuses overwrite unless `--force`; stdout-only output remains
read-only. `--attempt-id` supports deterministic tests and external
dispatchers. Readers accept v1/v2; writers emit v3. Legacy output requires
`--legacy-version 1|2`, and v1 cannot discard required v4 policy.

## ReceiptSubject/v1

Every new evaluation, graded, human, environment, or engine receipt binds the
same five subject fields: task, revision, authorization, attempt, and base
commit. Portable/human-authorized non-deterministic receipts also require a
trusted Ed25519 evaluator signature.

## AcceptanceRecord/v1

On success, acceptance atomically creates:

```text
.taskspec/acceptance/<task-id>/<attempt-id>.json
```

The record contains the subject, stable accepted outcome code, gate outcomes,
receipt paths and digests,
acceptance tier, acceptor, timestamp, optional supervision, and optional
verifier signature. The task then receives the complete envelope:

```yaml
accepted: true
accepted_by: verifier
accepted_at: <UTC timestamp>
accepted_tier: 1
accepted_attempt_id: <UUID>
accepted_authorization_ref: hmac-sha256-v3:…
acceptance_record_digest: sha256:…
```

The same attempt is idempotent only when subject, tier, acceptor, receipts,
supervision, and verifier signature are identical. A conflicting retry fails
without changing either the record or task envelope. A crash after the record but before task stamp
leaves an orphan record that `taskspec doctor --backlog` reports; retrying the
same attempt completes it. A metrics append failure never rolls back canonical
acceptance and is reported as a missing projection event.

Tier 2 is explicit:

```bash
taskspec accept --handoff attempt.json --stamp \
  --allow-tier2 --supervised-by reviewer \
  --reason "legacy authorization under supervised migration" \
  tasks/T-…-leaf.md
```

Failures use stable `AcceptanceFailure/v1` codes under global `--json`.
