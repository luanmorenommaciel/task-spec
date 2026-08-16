# Getting started

Task-Spec separates three decisions: what should exist, what one executor may
change, and what independent evidence will count as done.

1. [Install for your harness](installation.md).
2. [Create and accept the first atomic task](first-task.md).
3. [Review the complete release evidence in five minutes](reviewer-route.md).
4. [Run authorized leaves with optional TaskMesh](taskmesh.md).
5. Keep [the CLI reference](../reference/cli.md) nearby until the installed
   skill makes the mechanics familiar.

The shortest safe setup is:

```bash
taskspec init
taskspec setup signing
taskspec doctor
taskspec demo
taskspec setup
```

`taskspec demo` proves the full plan → gate → handoff → execute → accept loop in
an isolated disposable repository before you use the engine on real work.
`taskspec setup` always ends with one `NEXT:` line. A missing signing key is not
hidden: operation remains supervised Tier 2 until the key exists.

After authorizing a real task, persist its `TaskHandoff/v3` and pass that same
file to acceptance. This is what binds the Git base, attempt, receipts, and
acceptance record to one revision.
