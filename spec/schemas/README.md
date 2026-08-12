# Machine-readable contracts

All schemas use JSON Schema draft 2020-12. The Bash/Python gates remain the
operational authority for filesystem, HMAC, eval, and lifecycle behavior that a
structural schema cannot prove.

| Schema | Contract |
|---|---|
| [`task-spec-frontmatter.schema.json`](task-spec-frontmatter.schema.json) | Opt-in format-v4 evidence policy plus compatible v1-v3 frontmatter |
| [`agent-contract.schema.json`](agent-contract.schema.json) | Validation Card success criteria, retry policy, and executor contract |
| [`task-plan.schema.json`](task-plan.schema.json) | Complete deterministic authoring manifest consumed by `plan` and `batch --plan` |
| [`task-handoff.schema.json`](task-handoff.schema.json) | Read-only credential-free executor handoff |
| [`authoring-evidence.schema.json`](authoring-evidence.schema.json) | Optional provider-neutral research evidence |
| [`holdout-bundle.schema.json`](holdout-bundle.schema.json) / [`holdout-descriptor.schema.json`](holdout-descriptor.schema.json) | Hidden evaluator checks and executor-safe commitment |
| [`evaluation-receipt.schema.json`](evaluation-receipt.schema.json) | Deterministic or holdout evaluation result |
| [`graded-evaluation-receipt.schema.json`](graded-evaluation-receipt.schema.json) / [`human-acceptance-receipt.schema.json`](human-acceptance-receipt.schema.json) | Graded and accountable human decisions |
| [`environment-contract.schema.json`](environment-contract.schema.json) / [`environment-receipt.schema.json`](environment-receipt.schema.json) | Declared and enforced runtime boundary |
| [`engine-run-receipt.schema.json`](engine-run-receipt.schema.json) | Provider/model/adapter/run provenance |
| [`authorization-receipt.schema.json`](authorization-receipt.schema.json) | Optional Ed25519 identity above repository HMAC |
| [`a2a-artifact.schema.json`](a2a-artifact.schema.json) / [`mcp-task.schema.json`](mcp-task.schema.json) | Identity-preserving interoperability envelopes |

The two embedded Task-Spec schemas are also emitted through the stable CLI:

```bash
taskspec validate --emit-schema frontmatter
taskspec validate --emit-schema agent-contract
```

Format changes update schemas, conformance fixtures, templates, validator,
examples, and changelog together. Engine 3.7 preserves format v3 and offers
format v4 only when an author selects `taskspec new --format 4`.
