# Effort Gate

> **Purpose**: XS/S/M/L/XL classification + engine-aware routing. The size-based safety primitive.
> **Confidence**: HIGH
> **MCP Validated**: 2026-05-19 (size↔engine mapping added 2026-07-06, v3.2)

## The rule (v3.2 — size-tiered, engine-aware)

The gate maps t-shirt size to a **recommended engine** AND enforces atomicity. Small work
is atomic and portable; L is the boundary case a long-horizon engine can hold as ONE
coherent spec; XL and beyond are too big for a single machine-checkable done-condition and
route to SDD.

```text
XS → Task-Spec ✅  → recommend Kimi   (sprinter: fast atomic crank)
S  → Task-Spec ✅  → recommend Kimi
M  → Task-Spec ✅  → recommend Kimi
L  → Task-Spec ✅* → recommend GLM    (marathoner: long-horizon builder)
     *ACCEPTED ONLY with execution_backend: glm, AND it must still carry ONE
      coherent done-condition. If it needs multiple independent evals → decompose.
XL → Task-Spec ❌  → route to SDD: AgentSpec / OpenSpec / SpecKit
     ("XXL" and anything larger live here too — XL is the top t-shirt tier.)
```

**Why the recommendation is advisory, not a spec requirement.** The size→engine map is a
*dispatcher heuristic*, not a hard field. A spec names a `execution_backend` (a backend), and
the agent contract treats the model inside that backend as a black box (clause C9). "Kimi =
sprinter, GLM = marathoner" is fleet-level dispatch advice — it never overrides an author's
explicit backend choice, and it keeps the spec portable (see agent-contract.md, the
portability proof).

**Why L is gated to glm specifically.** L is the one tier where relaxing atomicity is
defensible: a 3–7 day task can occasionally have a single coherent done-condition that a
1M-context, long-horizon engine (GLM) can hold across hundreds of tool-call rounds. That
capability does not exist for every backend, so an L spec is accepted **only** when it
declares `execution_backend: glm`. Any other backend at L is refused — decompose into S/M
atoms (which then recommend GLM anyway) or route to SDD. The relaxation is narrow and loud,
never silent.

## The definitions

| Class | Time scope | Effort signal | Recommended engine | Example |
|-------|-----------|---------------|--------------------|---------|
| **XS** | ≤ 2 hours | Trivial one-liner / config tweak | Kimi | Bump a dependency; fix a typo in a constant |
| **S** | ≤ 1 day | One file or 2-3 closely-related files | Kimi | Add a /health endpoint |
| **M** | 1-3 days | Module-level change, multiple coordinated files | Kimi | Refactor a parser; add a new endpoint family |
| **L** | 3-7 days | Major migration held as ONE coherent goal | **GLM** (required backend) | Migrate one service to a new client, end-to-end |
| **XL** | > 1 week | Multi-team / multi-quarter → **not a Task-Spec** | SDD (route out) | Platform rewrite; org-wide rollout |

## Why the gate matters

| Property | XS/S/M (Kimi) | L (GLM, one coherent goal) | XL+ (SDD) |
|----------|---------------|----------------------------|-----------|
| Eval loop overhead | Amortized over small surface | Bounded — single done-condition | Crushing — too many things to verify |
| Human alignment cost | Small | Moderate — one goal, no design phases | Large — needs design phases |
| Single PR fits | Yes | Usually | No |
| Autonomous overnight execution | Sane | Sane on GLM (long-horizon) | Risky |
| Recovery if it fails | Park, retry tomorrow | Park, resume the GLM session | Major incident |

EDD's velocity advantage holds for XS/S/M on a sprinter (Kimi). L is the boundary a
long-horizon builder (GLM) can hold as one coherent spec. For XL and beyond, the spec phase
IS the work — and SDD's 5-phase rigor handles that better.

## The classifier (task-architect agent)

The `task-architect` agent applies these heuristics:

```text
SIGNAL                                      → IMPLIES
─────────────────────────────────────────────────────
Trivial one-liner / config tweak            → XS
1 file changes                              → S
2-5 closely-related files                   → S or small M
Multiple modules touched                    → M
New top-level directory                     → likely L (→ GLM, one coherent goal)
Cross-language change                       → likely L
New service / new deployment unit           → L or XL
"big" / "huge" / "platform" in intent       → likely XL
Multi-team coordination required            → XL
```

**XS/S/M** → accept, recommend Kimi.

**L** → accept ONLY with `execution_backend: glm`, and only if the task still has ONE
coherent done-condition. If it needs several independent evals, it is really multiple M
tasks — DECOMPOSE (the atoms then recommend GLM too). If the classifier returns L and the
backend is not glm, the agent outputs:

```text
This task is L effort.

An L Task-Spec is accepted only with execution_backend: glm (the long-horizon builder),
and it must still have a single coherent done-condition. Your options:
  1. Set execution_backend: glm  (if this is one coherent goal), or
  2. Decompose into S/M atoms     (dispatch the atoms to GLM), or
  3. Route to SDD                 (if the design itself is the work).
```

If the classifier returns **XL**, the agent REFUSES and outputs:

```text
This task is XL effort — too big for a single Task-Spec.

Route to a spec-driven (SDD) flow designed for large work:
  · AgentSpec  →  /agentspec:brainstorm "<your intent>"   (5-phase: brainstorm → define → design → build → ship)
  · OpenSpec   →  an OpenSpec proposal
  · SpecKit    →  a SpecKit specification

Decompose the SDD's build phase into S/M Task-Spec atoms when you reach implementation.
```

## Edge cases

### "It's actually two tasks"

If a task feels L because it's two M tasks bundled — DECOMPOSE.

```text
Original (L): "Migrate auth from JWT to OAuth2 across all services"

Decomposed:
  T-1 (M): Add OAuth2 provider in auth-service
  T-2 (M): Switch user-service to OAuth2 client
  T-3 (M): Switch admin-service to OAuth2 client
  T-4 (S): Remove JWT code paths after migration verified
```

Decomposition restores Task-Spec eligibility.

### "It LOOKS small but actually isn't"

Some 1-file changes are L in disguise — touching a critical, fragile module.
Use repo-scan heuristics:

```text
RED FLAGS for "looks S but actually L":
  · File has > 500 lines and high test coverage (sensitive code)
  · File appears in CODEOWNERS with many reviewers
  · File is in src/core/, src/auth/, src/billing/ (high-stakes paths)
  · Last 5 commits touching the file all required follow-up fixes
```

When in doubt, classify UP (S→M or M→L). False S→M produces overengineered specs; false M→L routes to AgentSpec, which is fine.

### "I want to override and use Task-Spec anyway"

For **XL**: don't. The gate refuses XL (doesn't ask) — bypassing it is how you get
half-baked specs for half-baked work. Route to SDD.

For **L**: the gate does not refuse outright — it requires `execution_backend: glm` AND a
single coherent done-condition. That is the override, and it is deliberate and narrow. Do
not reach for it to smuggle two M tasks into one L spec; if the done-condition needs several
independent evals, DECOMPOSE. The `--gold-sanity` acceptance gate will expose a non-atomic L
spec whose evals don't jointly discriminate.

## Related

- [task-spec-v1.md](../../spec/task-spec-v3.md) — frontmatter spec for `effort` field
- [edd-vs-sdd-honest-comparison.md](edd-vs-sdd-honest-comparison.md) — when each wins
- [agent-contract.md](agent-contract.md) — how the agent refuses
