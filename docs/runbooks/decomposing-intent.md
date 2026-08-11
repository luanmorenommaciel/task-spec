# Runbook: Decomposing Intent into Atomic Task-Specs

> **Use when:** you have a fuzzy intent, a PRD/design, or "a set of calls" that is
> too big for one atomic spec, and you need N linked Task-Specs that each pass the
> safe-to-delegate gate on their own. This is the canonical TaskPlan fan-out
> runbook; the legacy intent-file batch mode remains documented separately.

## Why decompose

One runnable leaf must be atomic — XS/S/M/L effort, one bounded write surface,
and evals that prove one coherent unit of work. XL/XXL nodes compose children
without owning writes. A PRD or a multi-step intent is none of those. Decomposition turns
the big thing into a flat set of atoms plus the edges between them, so each atom
can be authored, gated, and dispatched independently. See
[concepts/decomposition.md](../concepts/decomposition.md)
for the concept and the index+detail shape.

## Inputs

- A parent artifact: a PRD, a design doc, a meeting note, or a paragraph of intent
- (optional) a known target codebase, if the atoms touch in-repo paths

## The method (TaskPlan preview + generated detail)

The TaskPlan is the human-reviewable map. It declares leaves, XL/XXL nodes,
children, dependency edges, write surfaces, and holes before any spec is written.

### Step 1 — Use the installed skill to find the units

Give the parent artifact to the installed Task-Spec skill. Ask for a complete
`TaskPlan/v1`, not generated specs: every unit needs an id, one coherent goal,
size/profile/backend, write surface, evals, dependencies/children, and any open
question it could not resolve from repository evidence.

The preview should make the graph obvious:

```text
slug                  depends_on        hole?
extract-otel-config   []                (none)
wire-collector        [extract-otel-config]   which exporter endpoint? (BLOCKER)
verify-trace-lands    [wire-collector]  (none)
```

### Step 2 — Review the TaskPlan

Store the proposal under `tasks/.plans/` and preview it without mutation:

```bash
taskspec plan --manifest tasks/.plans/observability.yaml
```

Resolve dangling edges, cycles, dual creation, unordered shared writes, missing
behaviors/evals, and unresolved holes. Set `approved: true` only after that
review.

### Step 3 — Generate the declared specs

Generation materializes exactly the manifest; it never invents missing work:

```bash
taskspec batch --plan tasks/.plans/observability.yaml
taskspec validate tasks/T-*.md
taskspec dod tasks/T-*.md
```

### Step 4 — Inspect the generated edges and parent

In each generated detail spec, fill two frontmatter fields that turn the flat
list into a graph:

- **`parent:`** — the path/url of the index or the source PRD. The detail spec
  DISTILLS the parent; it never copies it. The validator resolves repo-relative
  `parent:` paths.
- **`depends_on:`** — the slugs of atoms that must finish first. The validator
  confirms every `depends_on` references an existing task.

### Step 5 — Mark the holes (first-class blockers)

An unresolved open question is **not** a footnote — it is a blocker that makes the
atom NOT safe-to-delegate. Encode every hole two ways:

1. **Machine-readable:** set `status: blocked` and fill `blocked_reason:` with the
   hole. The validator maps `blocked` → A2A `input-required` via `ts_a2a_state()`
   in `_lib.sh` — so an A2A-aware dispatcher sees the atom is waiting on input,
   not ready to run.
2. **Human-readable:** write the question in the `## Open Questions` zone (keep it
   non-`(none)`). That is the prose a human resolves before unblocking.

A `blocked` atom is not `ready`, so a backlog picker (`list-ready.sh`) will not
hand it to an executor. When the hole is answered, transition it:

```bash
taskspec transition \
    T-YYYYMMDD-wire-collector ready "endpoint confirmed: /api/public/otel/v1/traces"
```

Only then does the atom become eligible for the safe-to-delegate gate.

### Step 6 — Gate each atom independently

Each detail spec runs the normal pre-gate. A `ready` atom with no holes:

```bash
taskspec gate --stamp \
    tasks/T-YYYYMMDD-extract-otel-config.md
```

A `blocked` atom is intentionally NOT gated — its hole is unresolved. Leaving it
`blocked` is the correct, honest state. The gate (`safe-to-delegate.sh`) remains
the only path to `signed_off: true`; decomposition does not bypass it.

## Expressing a hole the validator already surfaces

No new script behavior is required. The hole convention reuses existing fields:

| Field | Value for an open hole | Effect |
|-------|------------------------|--------|
| `status:` | `blocked` | validator maps → A2A `input-required`; not `ready`, so not picked up |
| `blocked_reason:` | the one-line question | machine-readable blocker reason |
| `## Open Questions` | non-`(none)` prose | human-readable hole to resolve |
| `depends_on:` | upstream atom slugs | validator confirms edges resolve |
| `parent:` | PRD/index path | validator confirms the link resolves |

A reviewer verifies the convention held by running the validator and reading the
A2A line it prints:

```bash
# A holed atom must report A2A: input-required (NOT submitted/ready):
taskspec validate \
    tasks/T-YYYYMMDD-wire-collector.md | grep 'A2A: input-required'

# And it must NOT appear in the ready list:
taskspec ready | grep -q wire-collector \
    && echo "BUG: holed atom is delegate-eligible" || echo "OK: holed atom withheld"
```

## Anti-patterns

- **Don't hide work in a deep tree.** Use explicit XL/XXL nodes and a visible
  dependency DAG; nodes never own writes or reach the executor.
- **Don't bury a blocker in prose only.** An `## Open Questions` note with
  `status: ready` is a lie to the gate — the atom looks delegate-safe but isn't.
  Always pair the prose with `status: blocked`.
- **Don't copy the PRD into each atom.** Reference it via `parent:`; Zone 1
  carries only the one-paragraph distillation needed to execute the atom.
- **Don't re-implement batch generation.** `taskspec batch --plan` materializes
  the reviewed manifest exactly; repair the manifest when a generated unit is wrong.

## Remember

> **"Decomposition makes the graph explicit and the holes honest: each atom picks
> its own profile, declares its edges, and refuses to be delegated while a
> question is still open."**
