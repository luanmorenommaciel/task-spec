# TaskGraphView/v1

`TaskGraphView/v1` is a content-addressed, read-only projection. The shared
resolver scans `tasks/` recursively, including future nested lifecycle buckets. Markdown
Task-Specs and Git remain authoritative; Task-Spec does not add a graph database
or scheduler.

The resolver scans every lifecycle bucket and derives:

- task revision, status, effort, and write surface;
- normative `depends_on`, composition `children`, and optional `supersedes`;
- named cycles, dangling references, invalid composition, and dual-create
  collisions;
- ready frontier, blocked reasons, write conflicts, and deterministic
  write-disjoint groups;
- graph revision plus a dependency-closure digest for each selected leaf.

The closure contains the leaf, transitive dependencies, and composition
ancestors that contain the leaf as `(task_id, TaskRevision/v1)` pairs. A
composition ancestor's own dependencies are not pulled into the leaf closure.
It excludes mutable lifecycle
status, unrelated tasks, trackers, receipts, and scheduler state. A conflict
with an `in-progress` task is checked at handoff and acceptance, but does not invalidate every
signed leaf when an unrelated task appears.

```bash
taskspec graph
taskspec graph --check
taskspec graph --task T-…-leaf --json
taskspec graph --mermaid
```

`--check` exits nonzero for cycles, dangling references, duplicate IDs,
dual-creation collisions, or invalid composition. The command never writes,
schedules, or transitions a task.

The schema is
[`task-graph-view.schema.json`](../../spec/schemas/task-graph-view.schema.json).
