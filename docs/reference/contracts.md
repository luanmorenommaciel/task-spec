# Portable contracts

| Contract | Normative schema | Producer | Consumer |
|---|---|---|---|
| Task-Spec v3/v4 | [`task-spec-frontmatter.schema.json`](../../spec/schemas/task-spec-frontmatter.schema.json) | Skill/CLI | Gates and executors |
| TaskRevision v1 | [`task-revision.schema.json`](../../spec/schemas/task-revision.schema.json) | Canonicalizer | Authorization, handoff, graph, receipts |
| TaskPlan v1 | [`task-plan.schema.json`](../../spec/schemas/task-plan.schema.json) | Installed skill | `taskspec plan` / `batch --plan` |
| TaskMaterializationReceipt v1 | [`task-materialization-receipt.schema.json`](../../spec/schemas/task-materialization-receipt.schema.json) | `taskspec batch --plan` | External compilers and orchestrators |
| TaskHandoff v1/v2/v3 | [`task-handoff.schema.json`](../../spec/schemas/task-handoff.schema.json) | `taskspec handoff` | Any harness |
| TaskGraphView v1 | [`task-graph-view.schema.json`](../../spec/schemas/task-graph-view.schema.json) | `taskspec graph` | Lifecycle commands and external planners |
| TaskStatus v1 | [`task-status.schema.json`](../../spec/schemas/task-status.schema.json) | `taskspec status` | Humans, harnesses, and adapters |
| AuthoringEvidence v1 | [`authoring-evidence.schema.json`](../../spec/schemas/authoring-evidence.schema.json) | Optional provider pack | Installed skill/human reviewer |
| Agent context v1 | `taskspec agent-context` | CLI | Coding agents and adapters |
| Holdout bundle/descriptor | [`holdout-bundle.schema.json`](../../spec/schemas/holdout-bundle.schema.json) | Independent evaluator | Acceptance gate |
| Evaluation receipts | [`evaluation-receipt.schema.json`](../../spec/schemas/evaluation-receipt.schema.json) and companion receipt schemas | Evaluators, humans, environments, engines | Acceptance and evidence analysis |
| ReceiptSubject v1 | [`receipt-subject.schema.json`](../../spec/schemas/receipt-subject.schema.json) | v2 receipt writers | Acceptance policy |
| AcceptanceRecord v1 | [`acceptance-record.schema.json`](../../spec/schemas/acceptance-record.schema.json) | `taskspec accept --stamp` | Doctor, status, audit tooling |
| AcceptanceFailure v1 | [`acceptance-failure.schema.json`](../../spec/schemas/acceptance-failure.schema.json) | `taskspec --json accept` | Automation |
| EvaluatorTrust v1 | [`evaluator-trust.schema.json`](../../spec/schemas/evaluator-trust.schema.json) | Repository trust owner | Portable receipt verifier |
| MutationMatrix v1 | [`mutation-matrix.schema.json`](../../spec/schemas/mutation-matrix.schema.json) | Optional stack pack | `taskspec eval-audit --mutations` |
| QualityRubric v1 | [`quality-rubric.schema.json`](../../spec/schemas/quality-rubric.schema.json) | Release owner | Evidence-backed score generator |
| TaskSpecQualityScorecard v1 | [`task-spec-quality-scorecard.schema.json`](../../spec/schemas/task-spec-quality-scorecard.schema.json) | `make release-audit` | README status and reviewers |
| TaskSpecReleaseEvidence v2 | [`task-spec-release-evidence.schema.json`](../../spec/schemas/task-spec-release-evidence.schema.json) | Release audit | Publication and installer gates |
| EngineMatrix v2 / Result v2 | [`engine-matrix.schema.json`](../../spec/schemas/engine-matrix.schema.json) / [`engine-matrix-result.schema.json`](../../spec/schemas/engine-matrix-result.schema.json) | Evidence harness | Release audit |
| ProtocolConformanceEvidence v1 | [`protocol-conformance-evidence.schema.json`](../../spec/schemas/protocol-conformance-evidence.schema.json) | Pinned external SDK tests | Release audit |
| EnvironmentAttestation v1 | [`environment-attestation.schema.json`](../../spec/schemas/environment-attestation.schema.json) | External sandbox attestor | EnvironmentReceipt v2 and release audit |

The schemas document structure; the CLI performs the operational checks that a
JSON Schema cannot, including filesystem scope, HMAC/identity verification,
dependency state, eval discrimination, receipt binding, and acceptance ordering.
`TaskMaterializationReceipt/v1` reports `changed: false` for an exact rerun;
partial output sets and conflicting existing bytes are rejected without writes.
Optional A2A/MCP bridge metadata carries a canonical `handoff_digest`; changing
any embedded scope, budget, authorization, revision, or evidence requirement
breaks bridge validation.

Release evidence is deliberately stricter than a status badge. Every awarded
quality point references a retained artifact digest and an evidence class.
`pending`, `not_run`, `unavailable`, `fail`, or digest-mismatched evidence earns
no points; operational score generation also verifies totals and rubric
falsifiers that structural JSON Schema cannot calculate.
