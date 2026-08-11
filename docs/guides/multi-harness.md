# Multi-harness execution

Multi-harness means one portable handoff, not a fleet scheduler.

```bash
taskspec handoff tasks/T-…-leaf.md --backend codex
taskspec handoff tasks/T-…-leaf.md --backend claude
taskspec handoff tasks/T-…-leaf.md --backend kimi
```

`TaskHandoff/v1` carries the spec digest, verified sign-off tier, selected
backend, workspace, write scope, budgets, normalized agent contract, eval
command, and acceptance command. It never contains credentials and never starts
a model. The receiver must reject nodes and respect a sealed specific backend;
only `execution_backend: any` permits selection at handoff time.
