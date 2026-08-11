# Portable contracts

| Contract | Normative schema | Producer | Consumer |
|---|---|---|---|
| Task-Spec v3 | [`task-spec-frontmatter.schema.json`](../../spec/schemas/task-spec-frontmatter.schema.json) | Skill/CLI | Gates and executors |
| TaskPlan v1 | [`task-plan.schema.json`](../../spec/schemas/task-plan.schema.json) | Installed skill | `taskspec plan` / `batch --plan` |
| TaskHandoff v1 | [`task-handoff.schema.json`](../../spec/schemas/task-handoff.schema.json) | `taskspec handoff` | Any harness |
| AuthoringEvidence v1 | [`authoring-evidence.schema.json`](../../spec/schemas/authoring-evidence.schema.json) | Optional provider pack | Installed skill/human reviewer |
| Agent context v1 | `taskspec agent-context` | CLI | Coding agents and adapters |

The schemas document structure; the CLI performs the operational checks that a
JSON Schema cannot, including filesystem scope, HMAC verification, dependency
state, eval discrimination, and acceptance ordering.
