# Machine-readable contracts

All schemas use JSON Schema draft 2020-12. The Bash/Python gates remain the
operational authority for filesystem, HMAC, eval, and lifecycle behavior that a
structural schema cannot prove.

| Schema | Contract |
|---|---|
| [`task-spec-frontmatter.schema.json`](task-spec-frontmatter.schema.json) | Opt-in format-v4 evidence policy plus compatible v1-v3 frontmatter |
| [`agent-contract.schema.json`](agent-contract.schema.json) | Validation Card success criteria, retry policy, and executor contract |
| [`task-plan.schema.json`](task-plan.schema.json) | Complete deterministic authoring manifest consumed by `plan` and `batch --plan` |
| [`task-materialization-receipt.schema.json`](task-materialization-receipt.schema.json) | Task-Spec-owned receipt binding an approved TaskPlan to generated task bytes without dispatch authority |
| [`task-handoff.schema.json`](task-handoff.schema.json) | Read-only credential-free executor handoff |
| [`task-revision.schema.json`](task-revision.schema.json) | Canonical authorized revision identity |
| [`task-graph-view.schema.json`](task-graph-view.schema.json) / [`task-status.schema.json`](task-status.schema.json) | Derived backlog graph and read-only lifecycle status |
| [`authoring-evidence.schema.json`](authoring-evidence.schema.json) | Optional provider-neutral research evidence |
| [`holdout-bundle.schema.json`](holdout-bundle.schema.json) / [`holdout-descriptor.schema.json`](holdout-descriptor.schema.json) | Hidden evaluator checks and executor-safe commitment |
| [`evaluation-receipt.schema.json`](evaluation-receipt.schema.json) | Deterministic or holdout evaluation result |
| [`graded-evaluation-receipt.schema.json`](graded-evaluation-receipt.schema.json) / [`human-acceptance-receipt.schema.json`](human-acceptance-receipt.schema.json) | Graded and accountable human decisions |
| [`environment-contract.schema.json`](environment-contract.schema.json) / [`environment-receipt.schema.json`](environment-receipt.schema.json) | Declared and enforced runtime boundary |
| [`engine-run-receipt.schema.json`](engine-run-receipt.schema.json) | Provider/model/adapter/run provenance |
| [`receipt-subject.schema.json`](receipt-subject.schema.json) | Revision/authorization/attempt/base subject shared by v2 receipts |
| [`authorization-receipt.schema.json`](authorization-receipt.schema.json) | Optional Ed25519 identity above repository HMAC |
| [`evaluator-trust.schema.json`](evaluator-trust.schema.json) | Public evaluator keys scoped to receipt classes |
| [`acceptance-record.schema.json`](acceptance-record.schema.json) / [`acceptance-failure.schema.json`](acceptance-failure.schema.json) | Durable acceptance evidence and stable rejection codes |
| [`provider-smoke-evidence.schema.json`](provider-smoke-evidence.schema.json) | Live research-adapter graduation evidence |
| [`mutation-matrix.schema.json`](mutation-matrix.schema.json) | Experimental stack-specific eval falsifiers |
| [`a2a-artifact.schema.json`](a2a-artifact.schema.json) / [`mcp-task.schema.json`](mcp-task.schema.json) | Identity-preserving interoperability envelopes |
| [`quality-rubric.schema.json`](quality-rubric.schema.json) / [`task-spec-quality-scorecard.schema.json`](task-spec-quality-scorecard.schema.json) | Fixed quality criteria and evidence-derived score projection |
| [`task-spec-release-evidence.schema.json`](task-spec-release-evidence.schema.json) | Local, hosted, published, external, and unavailable release truth |
| [`engine-matrix.schema.json`](engine-matrix.schema.json) / [`engine-matrix-result.schema.json`](engine-matrix-result.schema.json) | Frozen real-engine benchmark and immutable outcomes |
| [`protocol-conformance-evidence.schema.json`](protocol-conformance-evidence.schema.json) | Pinned official protocol/SDK execution evidence |
| [`environment-attestation.schema.json`](environment-attestation.schema.json) | Observed external sandbox configuration and enforcement result |
| [`taskmesh-api.schema.json`](taskmesh-api.schema.json) / [`taskmesh-run.schema.json`](taskmesh-run.schema.json) | Optional helper negotiation and durable run identity |
| [`executor-capability.schema.json`](executor-capability.schema.json) / [`dispatch-decision.schema.json`](dispatch-decision.schema.json) | Probed executor claims and deterministic routing evidence |
| [`run-lease.schema.json`](run-lease.schema.json) / [`taskmesh-event.schema.json`](taskmesh-event.schema.json) | Fenced attempt authority and ordered runtime events |
| [`taskmesh-view.schema.json`](taskmesh-view.schema.json) | Rebuildable cockpit projection |
| [`sandbox-evidence.schema.json`](sandbox-evidence.schema.json) / [`credential-lease.schema.json`](credential-lease.schema.json) | Attempt-bound isolation evidence and secret-free expiring capability metadata |

The two embedded Task-Spec schemas are also emitted through the stable CLI:

```bash
taskspec validate --emit-schema frontmatter
taskspec validate --emit-schema agent-contract
```

Format changes update schemas, conformance fixtures, templates, validator,
examples, and changelog together. Engine 3.9 preserves format v3 and offers
format v4 only when an author selects `taskspec new --format 4`.

`tests/test-schema-contracts.sh` resolves every local `$ref`, rejects duplicate
schema IDs, and validates checked-in/generated contract fixtures using only the
Python standard library. `tests/test-release-evidence-contracts.sh` additionally
proves that missing digests, absolute artifact paths, and stale contract names
fail closed.
