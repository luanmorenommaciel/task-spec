# The authorization contract

`taskspec gate --stamp <spec>` is the only supported writer of Task-Spec
authorization. It validates the contract and eval shell, then atomically writes:

```yaml
signed_off: true
signed_off_by: <identity>
signed_off_at: <UTC timestamp>
signed_off_sig: hmac-sha256-v3:<key-id>:<mac>
```

## What HMAC v3 seals

The signature authorizes `TaskRevision/v1`, not a selected field list:

```text
task_revision_digest = sha256(
  "TaskRevision/v1\n" +
  task_id + "\n" +
  body_digest + "\n" +
  authority_manifest_digest
)
```

The authority manifest is canonical JSON derived from the complete
frontmatter. Only explicitly operational fields are excluded: lifecycle,
ownership/planning metadata, tracker projections, the authorization envelope,
and acceptance bookkeeping. Unknown future fields are sealed by default.

Canonicalization rejects duplicate YAML keys, aliases, unsupported tags, and
ambiguous scalars; mapping keys are sorted and list order is preserved. A body,
scope, dependency, graph-composition, proof-policy, environment-policy,
backend, budget, or future-field change retires the old authorization.

## The trust tiers

| Tier | Condition | What may happen |
|---:|---|---|
| 1 | HMAC v3 verifies with the repository-private key | Blind delegation and Tier-1 acceptance may proceed if every other gate passes |
| 2 | Key unavailable, blast radius skipped, legacy HMAC v1/v2, or legacy receipt | Supervised use only; acceptance requires `--allow-tier2 --supervised-by … --reason …` |
| 3 | Missing, malformed, or mismatched authorization | Refuse delegation and acceptance |

Valid HMAC v1/v2 signatures remain readable on their historical payloads, but
they are authentic-but-narrow Tier 2. `taskspec gate --stamp` always writes v3.
There is no bulk restamp: review and reseal each active task deliberately.

```bash
taskspec doctor --backlog
taskspec gate --stamp tasks/T-…-leaf.md
```

The backlog doctor names every narrow seal and prints its exact restamp command.

## Key boundary

The key is resolved through Git's common directory, so worktrees share the
repository-private key without copying it into task files. The author/verifier
key must not enter an executor environment. HMAC is symmetric: it proves that a
key holder authorized a revision; it does not provide individual identity,
non-repudiation, sandboxing, or semantic correctness.

Optional Ed25519 evaluator signatures attribute external v2 receipts. They do
not replace the repository authorization or make a weak evaluator trustworthy.

## Authorization is not acceptance

The PRE-gate proves that one exact contract is ready to attempt. The POST-gate
must independently rerun proof, inspect repository drift, verify the handoff and
dependency closure, bind required receipts, and write `AcceptanceRecord/v1`.
Only then may the task receive a complete acceptance envelope and transition to
`done`.

See [Trust and operational boundaries](../trust/index.md),
[Task revision](../reference/task-revision.md), and
[Acceptance contracts](../reference/acceptance-contracts.md).
