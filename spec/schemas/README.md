# Machine-readable contracts

All schemas use JSON Schema draft 2020-12. The Bash/Python gates remain the
operational authority for filesystem, HMAC, eval, and lifecycle behavior that a
structural schema cannot prove.

| Schema | Contract |
|---|---|
| [`task-spec-frontmatter.schema.json`](task-spec-frontmatter.schema.json) | Format-v3 task frontmatter, six-tier effort, node composition, v1/v2 HMAC, acceptance ordering |
| [`agent-contract.schema.json`](agent-contract.schema.json) | Validation Card success criteria, retry policy, and executor contract |
| [`task-plan.schema.json`](task-plan.schema.json) | Complete deterministic authoring manifest consumed by `plan` and `batch --plan` |
| [`task-handoff.schema.json`](task-handoff.schema.json) | Read-only credential-free executor handoff |
| [`authoring-evidence.schema.json`](authoring-evidence.schema.json) | Optional provider-neutral research evidence |

The two embedded Task-Spec schemas are also emitted through the stable CLI:

```bash
taskspec validate --emit-schema frontmatter
taskspec validate --emit-schema agent-contract
```

Format changes update schemas, conformance fixtures, templates, validator,
examples, and changelog together. `format_version` remains `3` in engine 3.6.
