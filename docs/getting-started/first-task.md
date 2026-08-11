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
taskspec handoff tasks/T-20260811-add-search-command.md --backend codex
```

The harness receives `TaskHandoff/v1`, performs only the declared write, and
runs the provided eval command. A separate operator or CI step then runs:

```bash
taskspec accept --stamp tasks/T-20260811-add-search-command.md
taskspec transition T-20260811-add-search-command done
```

If an eval, scope check, or seal check fails, acceptance returns
`ACCEPTED=0`; record the named failure, repair it, or park the task.
