# Task-Spec Brand Brief

Round 01 · Stage 1 · logo-strategy approval gate

## Evidence boundary

This brief is grounded in the current repository checkout on 2026-08-03.

- The live engine reports version `3.4.0` from `VERSION` and
  `bash bin/taskspec version`.
- The normative contract is `spec/`, its schemas, and its conformance suite.
- `adapters/` is explicitly non-normative.
- `TODO.md` and `docs/roadmap.md` are proposals, not shipped claims.
- The current `README.md` edit and everything under `assets/` are local,
  uncommitted concept work. They are useful context, not approved identity.
- The current POST-gate reruns evals in the current worktree, checks the declared
  blast radius, and re-verifies the sign-off envelope. The optional
  `--gold-sanity` path creates an ephemeral baseline worktree. A universal
  “clean-checkout POST-gate” claim is therefore excluded from the brand promise.
- Green evals prove only what they assert. HMAC is tamper-evident, not
  non-repudiation. Conformance is earned by the suite, not by a compatibility
  claim. Humans still own intent and acceptance judgment.

## Category and product role

Task-Spec is an open unit-of-work contract for autonomous agentic systems. It is
not a general project-management brand, an agent brand, or a workflow
orchestrator. It turns one bounded job into a portable artifact whose definition
of done can be executed.

The format is Markdown plus YAML frontmatter, behavioral intent, guardrails, and
runnable Bash evals. The engine authors, validates, gates, runs, accepts, and
certifies compatible executors around that artifact.

## Primary audiences

1. Agent-platform and developer-tool builders who need a vendor-neutral unit of
   work.
2. Engineering leads and staff engineers delegating bounded work to autonomous
   executors.
3. Infrastructure, data, security, and software teams that require explicit
   scope, retry limits, and inspectable evidence.
4. Executor and adapter authors seeking a testable L0–L2 compatibility target.

## Functional promise

Define one atomic job, authorize it deliberately, and verify its completion with
executable evidence rather than an executor’s assertion.

## Emotional promise

Calm delegation. The operator should feel that the boundary is explicit, the
attempt is bounded, and the verdict is inspectable.

## Differentiating idea

The task file carries its own proof contract. Behavior and evals are linked
bidirectionally; the eval bodies are sealed at sign-off; acceptance reruns the
contract and checks scope. “Done” is a verdict produced by evidence, not a status
an agent is trusted to set.

## Trust model

- Runnable success criteria define the observable contract.
- Behavior-to-eval traceability prevents untested promises and stray tests.
- `signed_off: true` is delegation authorization, not completion.
- A keyed HMAC makes covered post-sign-off edits evident; shared-key holders can
  reseal, so it does not prove an individual signer.
- Tier 1 is keyed and verified; Tier 2 is structural-only and supervised; a
  mismatch is fail-closed.
- The POST-gate reruns evals, checks changed files against declared paths, and
  re-verifies the sign-off envelope before `accepted: true`.
- `--gold-sanity` can additionally require the eval set to fail on an unpatched
  baseline.
- L0–L2 conformance is observable: read/run, lifecycle, then bounded retry and
  parking.
- Humans remain responsible for intent quality and final acceptance judgment.

## Core product action

**Bind intent to executable proof inside one portable, bounded artifact.**

The practical sequence is:

`Author → Validate → PRE-gate → Execute → POST-gate → Accept`

The mark should compress that action into a symbol, not illustrate the whole
flowchart.

## Brand personality

- exact, not bureaucratic;
- calm, not passive;
- rigorous, not militarized;
- open and portable, not vendor-coded;
- technical, not “AI futuristic”;
- confident about evidence and candid about limits;
- compact, modular, and operational.

## Naming and casing

- Repository and general brand: `task-spec`
- Unit-of-work noun: `Task-Spec`
- CLI command: `taskspec`
- Display wordmark: `TASK-SPEC`
- The hyphen is mandatory in the unit noun and display wordmark.
- Do not normalize all contexts to one spelling.
- Do not use `TaskSpec`, `TASKSPEC`, or `Task Spec` as substitutes for the
  product or unit name.

The wordmark hyphen is more than punctuation: it visually reinforces the idea
that intent and proof are bound into one unit.

## Symbolic territory

Promising metaphors, derived from the product:

- an atomic cell held between PRE and POST thresholds;
- two traces locked together: behavior and eval;
- an open contract becoming a sealed, terminal artifact;
- a proof-bearing notch or closure that cannot be removed silently;
- a bounded chamber whose exit opens only on evidence;
- a portable unit that keeps the same internal contract across executors.

The symbol should be reducible to a strong one-color silhouette and remain
recognizable at 16 px.

## Visual territory to avoid

- clipboard, checklist, certificate, ordinary document, shield, padlock, or wax
  seal as the primary silhouette;
- a tiny checkmark used as the entire idea;
- atomic orbits, hexagon-plus-braces, network-node diagrams, sparks, or robot
  imagery;
- purple-blue “AI” gradients, glow-dependent marks, and fake code text;
- a lifecycle diagram disguised as a logo;
- Converge’s hexagonal fold/closing-loop geometry or Forge Gold system;
- Seamwise’s opposing architectural plates, luminous seam, branching rails, or
  cyan-led industrial atmosphere;
- Semattice’s framed “S”, layered ribbons, indigo/cyan/mint palette, or rounded
  modular-ribbon construction.

## Relationship to adjacent projects

| Brand | Role | Visual implication |
| --- | --- | --- |
| Seamwise | Discovers system seams, ownership, dependency-safe order, and emits reviewed, unsealed Task-Specs. | Architectural, upstream, plural, graph-aware. Task-Spec must look smaller, harder, and singular. |
| Task-Spec | Defines and authorizes one atomic, verifiable job. | Compact proof-bearing unit. The identity should feel like a portable contract or measured cell. |
| Converge | Governs the wider method, authorization, execution, evidence, settlement, and learning. | System-level and cyclical. Task-Spec must not borrow its fold, settlement loop, or gold/mint/coral identity. |

The three brands may share restraint, disciplined grids, and evidence-led
language, but their marks must remain unmistakably independent.

## Round 01 evaluation criteria

Advance the direction that best:

1. communicates one bounded proof-bearing unit without a diagram;
2. is distinctive beside Seamwise and Converge;
3. survives one color and 16 px;
4. supports a mandatory-hyphen `TASK-SPEC` wordmark;
5. avoids overclaiming the current implementation;
6. can be rebuilt as simple, controlled SVG geometry in Stage 2.
