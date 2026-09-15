# Native decomposition and review

Use `taskspec decompose prepare <id> --recipe <file>` to validate authored input
and propose topology. `--dry-run` produces diagnostics without changing the plan.
Each accepted seam owns one swimlane; each capability leg names an observable
state and proof; executable leaves own coherent done-conditions and bounded writes.
SDLC stages are concerns on the work, not mandatory lanes.

A blocked proposal is a valid planning outcome. Preserve `OPEN` objections and
`system_map.unknowns` when ownership, evidence, or product decisions are missing.
Keep the authored proposal and report the smallest unresolved decision; do not
clear unknowns or mark objections `ACCEPTED` or `FIXED` merely to make preparation
pass. Preserve references to applicable unresolved decisions as well; deleting
`decision_ids` does not resolve the decisions they name. Record resolution or
accepted risk only from an explicit applicable decision.
The reviewer's identity authenticates review; it does not assign seam or swimlane
ownership. Record actual owners in the recipe and prepare the corrected topology
before requesting review.

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
