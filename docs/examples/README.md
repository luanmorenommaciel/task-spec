# Examples

| Example | Demonstrates | Operational status |
|---|---|---|
| [`task-plan.yaml`](task-plan.yaml) | One reviewed S leaf with behavior-to-eval traceability | Runnable through `taskspec plan` and `taskspec batch` |
| [`composition-plan.yaml`](composition-plan.yaml) | XS/S/M/L leaves, XL/XXL nodes, children, and a dependency DAG | Runnable preview; generated specs still require human review before sealing |
| [`authoring-evidence.json`](authoring-evidence.json) | Provider-grounded context in the shared Exa-shaped offline contract | Valid fake evidence; no live-provider claim |
| [`task-handoff.json`](task-handoff.json) | Credential-free cross-harness transfer shape | Structural illustration; paths/digest are deliberately non-operational |

Preview the composition without writing files:

```bash
taskspec plan --manifest docs/examples/composition-plan.yaml
```

Generate only after copying it into the repository plan workspace, reviewing
every declared unit, and keeping `approved: true` as an explicit human choice.
