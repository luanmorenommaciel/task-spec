# Concept: Decomposition (intent → atoms)

> **Status:** normative (v3)
> **Runbook:** [../../runbooks/decomposing-intent.md](../runbooks/decomposing-intent.md)
> **Related fields:** `parent:`, `depends_on:`, `status: blocked`, `blocked_reason:`

## Why atomic decomposition

A Task-Spec is the *atomic* unit of work: an XS/S/M/L leaf has one bounded
write surface and evals that prove one coherent result; XL/XXL nodes compose
those leaves without owning writes. A PRD, a design doc, or "a set of calls" is none of
those — it is FEATURE altitude, with many outcomes and many edges. You cannot gate
a PRD; the Exit Check would have to assert a dozen unrelated facts at once, and a
failure would not tell you *which* unit is unbuilt.

Decomposition turns one FEATURE-altitude artifact into a reviewed `TaskPlan/v1`:
runnable leaves, explicit dependency edges, and optional XL/XXL composition
nodes. Each leaf can be gated and dispatched independently. The big thing stays
referenced; each unit carries only the distillation it needs.

## The shape: manifest + shallow composition + per-task detail

The canonical shape keeps the dependency DAG visible and limits composition to
reviewable nodes rather than an arbitrary nested work breakdown:

```
parent PRD/design ──referenced by──▶ TaskPlan v1
                                       ├─▶ XL/XXL node (reviewable, no writes)
                                       │      └─▶ child leaf (gateable)
                                       └─▶ leaf ──depends_on──▶ leaf
```

- The **TaskPlan** is the deterministic, human-skimmable proposal. Previewing
  it never creates or invents units.
- An **XL/XXL node** is a Task-Spec used for composition and review. It owns no
  write surface and is never handed to an executor.
- Each **leaf spec** has Goal, runnable Success Criteria, and an Exit Check that
  can pass the gate independently.

`taskspec plan` keeps children and `depends_on` visible together. Avoid deeper
nesting that obscures ordering or makes a node carry executable work.

## Holes as first-class blockers

The load-bearing rule: **an unresolved open question is a blocker, not a
footnote.** An atom with an open hole is NOT safe-to-delegate, because an executor
that runs it would have to *guess* the missing fact — exactly the silent-wrong
outcome the format exists to prevent.

A hole is encoded with fields that already exist:

- `status: blocked` — which the validator maps to the A2A `input-required` state
  (`ts_a2a_state()` in `_lib.sh`). An A2A-aware dispatcher reads this as "waiting
  on a human/upstream," not "ready."
- `blocked_reason:` — the one-line machine-readable question.
- a non-`(none)` `## Open Questions` zone — the human-readable hole to resolve.

Because a `blocked` atom is not `ready`, a backlog picker withholds it from
executors, and the gate is never run on it. When the hole is answered, the atom
transitions `blocked → ready` and *then* becomes eligible for the gate. This makes
"a question is still open" a structural property the tooling enforces, rather than
a comment a human might miss. The gate (`safe-to-delegate.sh`) remains the only
path to `signed_off: true` — decomposition never bypasses it; it only governs
*when* an atom is allowed to reach it.

## Relationship to profiles

Each atom **picks its own profile** ([profiles.md](profiles.md)). Decomposition
does not impose one profile on the whole set — that is the point of atomicity. A
low-blast-radius doc-fix atom can be `lite`; an unattended money-field atom in the
same decomposition is `full`. The parent artifact's overall severity does not
force every atom up; each atom escalates only on its own consequence.

## Relationship to depends_on (and parent)

Two edges turn the flat list into a graph:

- **`depends_on:`** — sibling edges between atoms. Atom B's `depends_on:
  [atom-a]` means B cannot start until A is `done`. The validator confirms every
  `depends_on` resolves to an existing task; `lint-backlog.sh` detects cycles
  across the set.
- **`parent:`** — the vertical edge up to the PRD/index. The atom DISTILLS the
  parent; the validator resolves repo-relative `parent:` paths. This is how an
  atom stays atomic while remaining traceable to the FEATURE it serves.

Together, `parent:` (up) and `depends_on:` (across) make the decomposition a
verifiable DAG: every atom knows where it came from and what must precede it, and
no atom is delegate-safe while it still holds an open hole.

## See also

- [../../runbooks/decomposing-intent.md](../runbooks/decomposing-intent.md) — the step-by-step method
- [profiles.md](profiles.md) — each atom picks its own profile
- [signed-off.md](signed-off.md) — the gate the atoms must each pass
- [conformance-levels.md](conformance-levels.md) — the A2A status mapping holes ride on
