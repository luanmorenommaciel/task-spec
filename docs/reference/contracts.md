# Portable contracts

| Contract | Normative schema | Producer | Consumer |
|---|---|---|---|
| Task-Spec v3/v4 | [`task-spec-frontmatter.schema.json`](../../spec/schemas/task-spec-frontmatter.schema.json) | Skill/CLI | Gates and executors |
| TaskPlan v1 | [`task-plan.schema.json`](../../spec/schemas/task-plan.schema.json) | Installed skill | `taskspec plan` / `batch --plan` |
| TaskHandoff v1/v2 | [`task-handoff.schema.json`](../../spec/schemas/task-handoff.schema.json) | `taskspec handoff` | Any harness |
| AuthoringEvidence v1 | [`authoring-evidence.schema.json`](../../spec/schemas/authoring-evidence.schema.json) | Optional provider pack | Installed skill/human reviewer |
| Agent context v1 | `taskspec agent-context` | CLI | Coding agents and adapters |
| Holdout bundle/descriptor | [`holdout-bundle.schema.json`](../../spec/schemas/holdout-bundle.schema.json) | Independent evaluator | Acceptance gate |
| Evaluation receipts | [`evaluation-receipt.schema.json`](../../spec/schemas/evaluation-receipt.schema.json) and companion receipt schemas | Evaluators, humans, environments, engines | Acceptance and evidence analysis |

The schemas document structure; the CLI performs the operational checks that a
JSON Schema cannot, including filesystem scope, HMAC/identity verification,
dependency state, eval discrimination, receipt binding, and acceptance ordering.
