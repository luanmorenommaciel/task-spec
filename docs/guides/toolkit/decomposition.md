# Native decomposition and review

Use `taskspec decompose prepare <id> --recipe <file>` to validate authored input
and propose topology. `--dry-run` produces diagnostics without changing the plan.
Each accepted seam owns one swimlane; each capability leg names an observable
state and proof; executable leaves own coherent done-conditions and bounded writes.
SDLC stages are concerns on the work, not mandatory lanes.

Read `tasks/.plans/<id>/delivery-plan.yaml`, proposed leg artifacts, and graph
before recording explicit human review:

```bash
taskspec decompose review <id> --accept --reviewer <identity> --reason <decision>
taskspec decompose compile <id>
taskspec plan --manifest tasks/.plans/<id>/task-plan.json
taskspec batch --plan tasks/.plans/<id>/task-plan.json
```

Review binds the complete topology through the repository HMAC key using the
plan-review domain. Compilation and materialization do not seal execution.
The authored recipe, immutable snapshots, native TaskPlanLineage/v1, bundle,
and existing materialization receipt retain the intent-to-leaf chain.

Before replanning, preserve the prior bundle path. Use `prepare --replace`, review,
compile, then `decompose impact <id> --against <prior-bundle.json>` to inspect
changed, added, removed, and unchanged projections. Relevant constraints, recipe,
dependencies, proof, and source changes require renewed authorization. Unrelated
sibling changes preserve the earlier snapshot for unchanged leaves.

Recipe task fields may include `execution_recipe` (a strategy name),
`shared_resources` (resource identifiers requiring serialization), and
`proves_capabilities` (leg IDs this integration-proof leaf independently evaluates).
Absence of a proof leaf leaves a capability unproven even when all children are done.

Optional `sdlc_stages` values are `plan`, `design`, `build`, `test`, `deploy`, and
`maintain`. One leaf may carry several concerns; these labels never create lanes
or replace required evals. Original intake text is retained in the review and
applicable leaf constraints. Import rollback is tested before materialization.
