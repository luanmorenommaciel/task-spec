# First atomic task

This is the complete lifecycle. The [example TaskPlan](../examples/task-plan.yaml)
declares every unit, path, behavior, eval, and edge; preview does not fill gaps.

```bash
taskspec init
taskspec setup signing

mkdir -p tasks/.plans
cp docs/examples/task-plan.yaml tasks/.plans/add-search.yaml

taskspec plan --manifest tasks/.plans/add-search.yaml
taskspec batch --plan tasks/.plans/add-search.yaml
taskspec validate tasks/T-20260811-add-search-command.md
taskspec dod tasks/T-20260811-add-search-command.md
taskspec gate --stamp tasks/T-20260811-add-search-command.md
taskspec handoff tasks/T-20260811-add-search-command.md --backend codex \
  --out .taskspec/handoffs/add-search.json
```

Every newly authorized leaf produces `TaskHandoff/v3`, including format v3.
The executor performs only the declared write and runs the provided eval. A
separate operator or CI step then uses the same handoff:

```bash
taskspec accept --stamp --handoff .taskspec/handoffs/add-search.json \
  tasks/T-20260811-add-search-command.md
taskspec transition T-20260811-add-search-command done
```

If an eval, committed/uncommitted scope check, revision, closure, or receipt
check fails, acceptance returns `ACCEPTED=0` and a stable failure code. Record
the named failure, replan/reauthor when authority changed, or park the task.

Choose `taskspec new --format 4 ...` only when acceptance needs independent
holdout, graded, human, environment, or identity evidence. The handoff remains
v3; see [the v4 specification](../../spec/task-spec-v4.md).
