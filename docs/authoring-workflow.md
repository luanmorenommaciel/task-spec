# Authoring workflow — the task-spec doctrine

> This is the **authoring doctrine** for the task-spec engine. The installer ships
> it as `references/authoring-workflow.md` inside every installed skill. It is
> invoked via the canonical root `SKILL.md`, the compatibility skill in
> [`harness/claude-code/`](../harness/claude-code/SKILL.md), or by
> calling the `taskspec` CLI directly. Script references below map to
> `bin/taskspec` subcommands (`new`, `batch`, `validate`, `gate`, `run`,
> `accept`, `transition`, `ready`, `rebuild-state`, `archive`, `backup`,
> `lint`, `metrics`, `conformance`); script files live under `src/<verb>/`.


> **Identity:** The open, atomic unit-of-work format for autonomous agentic systems
> **Domain:** Task PRD generation, eval-driven development, backlog management
> **Default Threshold:** severity-scaled (0.80–0.99) — see Threshold Mapping below

This skill is part of the **CAW Triad** for task generation:
- **C** (this Skill): the workflow + bundled scripts + templates
- **A** (Agent): `task-architect` — applies Agreement Matrix, ensures quality
- **W** (MCPs): Context7, Exa, Ref — fresh validation at authoring time

---

## When to invoke this skill

Trigger conditions (Claude auto-invokes when context matches):
- User says "create a task," "scaffold a task," "decompose this into work"
- User has fuzzy intent ("verify the deploy pipeline works")
- User wants to convert a meeting note into actionable backlog
- User mentions Task-Spec, EDD, eval-driven, or "make this executable"
- User asks for a task that any conformant engine (e.g. Claude/Codex/Cursor) can pick up

Pause authoring if:
- The outcome is still too fuzzy to declare behaviors and discriminating evals
- An L leaf has multiple independent done-conditions (decompose it)
- Subjective output has no reviewable machine or human oracle yet
- User just wants a one-off prompt, not a reusable spec

---

## Workflow

```text
┌──────────────────────────────────────────────────────────────────┐
│  TASK-SPEC WORKFLOW                                               │
├──────────────────────────────────────────────────────────────────┤
│  Phase 1: UNDERSTAND    parse intent, classify effort             │
│  Phase 2: RESEARCH      optional AuthoringEvidence v1             │
│  Phase 3: SCAN          read host repo for touches_paths          │
│  Phase 4: ARCHITECT     spawn task-architect agent for judgment   │
│  Phase 5: COMPOSE       TaskPlan preview, then declared specs     │
│  Phase 6: VALIDATE      structural linter — validate-task-spec.sh │
│  Phase 7: GATE          PRE-gate — safe-to-delegate.sh --stamp    │
│  Phase 8: DISPATCH      hand off to executor per execution_backend│
│  Phase 9: ACCEPT        POST-gate — accept-task.sh --stamp        │
└──────────────────────────────────────────────────────────────────┘
```

> **The loop is closed (v3).** Phase 7 certifies the SPEC is delegate-safe (evals
> well-formed; assertion failure expected). Phase 9 certifies the WORK is real
> (evals now PASS from a clean checkout + change set within blast radius + sign-off
> HMAC intact). A task is provably DONE only when `accept-task.sh` writes
> `accepted: true`. Humans sit at Phase 1 (intent) and review the Phase 9 verdict —
> not in the middle of the execution loop. See
> [concepts/conformance-levels.md](concepts/conformance-levels.md).

> **Alternative: Batch Sprint Compose** — when you need N specs at once in a
> known domain, skip Phase 2 (MCP research) and Phase 4 (task-architect spawn).
> See [Batch Sprint Compose](#batch-sprint-compose-fast-batch) below.

### Phase 1 — Understand

Parse the user's intent. Critical questions answered before scaffolding:

1. **What's the verbal description?** (1 paragraph from user)
2. **Effort class?** XS/S/M/L are leaves; L needs one coherent done-condition and a configured long-horizon backend. XL/XXL are child-composing nodes, not executor work. See `concepts/effort-gate.md`.
3. **Agent hint?** `any` (vendor-portable) OR specific (`python-developer`, etc.)
4. **Source provenance?** Meeting note, audit, ticket — must have one
5. **Touches what paths?** Best guess; refined in Phase 3

If unclear, ASK ONCE for clarification. Don't proceed with vague intent.

### Phase 2 — Research (optional evidence)

When current external evidence is necessary, explicitly select a provider and
normalize its output to `AuthoringEvidence/v1`:

```text
Firecrawl / Tavily / Exa / another explicit provider → bounded, cited evidence
```

The research output feeds the `anti-patterns` and `do-not-touch` zones —
both should be informed by real-world failure modes from MCP findings.

### Phase 3 — Scan

Read the host repo to refine:
- Which files actually exist on `touches_paths`?
- Any cross-cutting concerns (touches the same files as in-flight tasks)?
- Existing conventions (CLAUDE.md, .editorconfig, project style)?

This uses Glob + Grep + Read in the host repo — no writes.

### Phase 4 — Architect (spawn the agent)

Spawn the **`task-architect`** agent with:
- The intent
- Phase 2 research findings
- Phase 3 repo scan findings

The agent:
- Applies Agreement Matrix (KB + MCP)
- Decides isolation class (worktree vs branch)
- Drafts the 3 evals as runnable bash
- Drafts anti-patterns + do-not-touch from research
- Returns a structured build plan with confidence score

If confidence < 0.95, ASK the user before composing.

### Phase 5 — Compose

Run `taskspec new` (src/author/generate-task-spec.sh) to create the T-*.md file from the template,
then fill in:

| Zone | What goes in |
|------|--------------|
| Frontmatter | id, title, status=ready, format_version=3, profile, effort, budget=15, agent, touches_paths, source_note |
| Zone 1 | Why / Goal / Context (lean) |
| Zone 2 | 3+ evals + validation_card YAML + exit_check bash |
| Zone 3 | Rollback Plan (or `(none)`) |
| Zone 4 | Observability Hooks (or `(none)`) |
| Zone 5 | Anti-patterns + do-not-touch list |
| Zone 6 | Open questions (or `(none)`) |

**Two shape rules govern every atom:**

- **Cut tracer bullets, not layers.** For feature work, prefer a **vertical
  slice** — a narrow but COMPLETE path through every layer the feature
  touches (schema → transform → serving → test), demoable or verifiable on
  its own — over a horizontal slice of one layer. A horizontal atom ("all the
  models", "all the endpoints") passes its own eval while proving nothing
  end-to-end; a tracer bullet's eval exercises the seam the system actually
  ships through. The eval defines *done*; the vertical cut defines *worth
  doing alone*.
- **Size to one fresh context window.** An atom must fit — spec, cited ADRs,
  touched files, and the working diff — inside a single fresh executor
  session. If holding the task means the executor must page out what it read,
  the atom is too big: split it and wire `depends_on`. This is the practical
  ceiling within each runnable XS/S/M/L leaf, not a new class.

**Layered policy (legacy tolerance):** `format_version` is `3` for new specs (the template's default; see `src/templates/task-spec.md.tpl`). Tasks created before 2026-05-27 (or explicitly marked `format_version: 0`, `1`, or `2`) are treated as legacy. The validator accepts legacy v0/v1/v2 tasks with warnings rather than hard failures, and the `migrate-legacy-task.sh` script converts legacy markdown checklists into runnable eval stubs.

### Phase 6 — Validate (pre-gate structural linter)

> **Validate is NOT the gate.** It is the structural linter that runs BEFORE the gate. It does not execute evals; it does not stamp `signed_off`. See [concepts/signed-off.md](concepts/signed-off.md) for the validate-vs-gate contract.

Run `taskspec validate tasks/T-*.md` (src/gate/validate-task-spec.sh):
- Confirms all 6 zones present
- Confirms all required frontmatter fields
- Confirms no `{{TODO}}` placeholders remain
- Confirms eval functions are syntactically valid bash
- Confirms `id` matches the filename basename
- Confirms every `depends_on` references an existing task (warns if target is parked/done)
- Confirms every `touches_paths` exists on disk (warns only if task is parked)
- Confirms Exit Check calls every `eval_N()` defined in Success Criteria
- For v2/v3 (which share the `agent_contract` v2 schema): confirms `agent_contract` has
  `produce` as YAML list, `emit` as enum list, `timeout_minutes` as 1–1440,
  `sandbox_type` as host|isolated|ephemeral, and `required_tools` as a non-empty list
- For v3 `profile: standard|full`: confirms a `## Behavior` section (Given/When/Then,
  `B-N` ids) exists and that every behavior is verified by ≥1 eval and every eval maps to
  a declared behavior (the behavior↔eval traceability lint)
- `--shellcheck-evals` (opt-in): pipes each `eval_N()` body through `shellcheck -S warning`
  to catch syntax errors and dead variables
- `--dry-run-eval` (opt-in): sources the bash blocks in a disposable subshell and verifies
  the Exit Check exits 0 against the current repo

**State invariant:** Every successful validation idempotently updates `tasks/_state.yaml` with the
 task's frontmatter snapshot, `last_validated` timestamp, and `validator_version`. Failed
 validations do **not** write state — broken specs never pollute the audit trail. If
 `_state.yaml` doesn't reflect a task file's frontmatter, the validator hasn't run on it
 OR `rebuild-state.sh` is overdue.

### Phase 7 — Gate (the autonomy contract)

**This is THE gate.** It is the only path to `signed_off: true`. Authors do not hand-edit `signed_off`; hand-stamping is rejected by the v2.1 structural sign-off envelope check.

Run `taskspec gate --stamp tasks/T-*.md` (src/gate/safe-to-delegate.sh):

- Composes `validate-task-spec.sh` (structural) + `run-task-spec.sh` (eval execution) into one go/no-go verdict
- `validate` must exit 0 (structural pass)
- Eval bodies must execute without bash-level errors (no `syntax error`, no `unbound variable`, no `command not found`, no inverted-grep-c footguns)
- Assertion failures are EXPECTED on an unbuilt task — the work isn't done yet. The gate fails for the RIGHT reason (assertion not yet true) not the WRONG reason (eval is broken bash)
- On success: flips `signed_off: false` → `signed_off: true`, stamps `signed_off_by: $USER` (override with `--stamp-by`), and records `signed_off_at: <iso-8601>`
- On failure: prints `VERDICT: DO NOT DELEGATE` and exits 1. The spec stays `signed_off: false`

`taskspec run` (src/gate/run-task-spec.sh) runs the evals directly (used by the gate; usually not invoked standalone):

- Extracts Success Criteria and Exit Check bash blocks
- Runs each `eval_N()` in an isolated subshell with `set -euo pipefail`
- Captures per-eval stdout/stderr/duration
- Reports `pass`/`fail` per eval with timing
- Exits 0 only when the Exit Check returns 0
- `--ci` flag emits one JSON line per eval for non-interactive pipelines

### Phase 8 — Dispatch

A spec with `signed_off: true` is ready to hand to an autonomous executor. See [runbooks/dispatching-a-task-spec.md](runbooks/dispatching-a-task-spec.md) for the full handoff protocol. *Optional debrief:* **`pass-to-lesson`** teaches the signed-off backlog — every field, the decision it encodes, what breaks downstream without it — before dispatch.

The spec's frontmatter carries an `execution_backend:` field that names the canonical
executor. **It is an OPEN STRING, not a closed enum** (validator treats any single token
as valid; see src/gate/validate-task-spec.sh): `any` (the default) defers to the author's
choice, and any other token names a specific executor. The bundled per-engine dispatch
adapters are the **non-normative** layer — they live in `../harness/engines/` and
each carries its own dispatch command:

| `execution_backend` value | Where to find the dispatch command |
|---------------------------|------------------------------------|
| `any` (default) | Author's choice — pick any conformant executor |
| named token (e.g. `claude`, `codex`, `kimi`, `cursor`, `taskship`, `anthive`) | the matching recipe in `../harness/engines/` |
| a token with no bundled recipe | `../harness/engines/custom.md` (DIY adapter) |

Report to user:

- File path + signed_off status
- Gate verdict (DELEGATE / DO NOT DELEGATE)
- Recommended dispatch command per `execution_backend`
- Optional: dispatch immediately if user said "and run it"

---

## Batch Sprint Compose (Fast Batch)

Use the **Fast Batch** path when you're decomposing a known audit or feature
into many atomic specs against an in-repo codebase. Skip the per-task MCP
research and architect spawn; compose directly from structured intent.

### When to use Fast Batch vs Full Workflow

| Criterion | Fast Batch | Full Workflow |
|-----------|------------|---------------|
| Domain familiarity | Known — you already understand the codebase | Unknown — greenfield task, unfamiliar library |
| MCP research value | Low — no external docs needed | High — need Context7 / Exa / Ref for failure modes |
| Intent structure | User provides `slug: description` per line | User gives a fuzzy paragraph |
| Task count | 3–20 specs at once | 1 spec at a time |
| Structural confidence | ≥ 0.95 — user already provided `touches_paths`, `evals`, etc. | < 0.95 — need task-architect to draft evals |
| Empirical signal | Prior batch validated first-try | Novel task with unknown failure modes |

**Decision rule:** If ≥ 4 of the 6 criteria above favor Fast Batch, use it.
Otherwise, run the full 6-phase workflow.

### Batch Sprint flow

```text
┌──────────────────────────────────────────────────────────────────┐
│  BATCH SPRINT COMPOSE                                             │
├──────────────────────────────────────────────────────────────────┤
│  Step 1: PREPARE        collect intent list (slug + description)  │
│  Step 2: GENERATE       batch-generate.sh → N stub T-*.md files   │
│  Step 3: FILL           edit stubs: title, why, goal, evals, etc. │
│  Step 4: BULK-VALIDATE  validate-task-spec.sh on each file        │
│  Step 5: COMMIT         git add tasks/ + state + metrics          │
└──────────────────────────────────────────────────────────────────┘
```

### Input format

One line per task in `slug: description` form:

```text
fix-login-redirect   Redirect to /dashboard after OAuth success instead of /
add-rate-limiting    Add 100 req/min rate limit to /api/v1/analyze endpoint
update-telemetry     Emit batch-completed event to Langfuse after each sprint
```

Save to a file (e.g. `intents.txt`) and run:

```bash
taskspec batch \
    --intent-file intents.txt \
    --effort S \
    --agent any \
    --queue
```

Flags:
- `--intent-file <path>` — required. File with one `slug: description` per line.
- `--effort S|M` — required. Applied to every generated spec.
- `--agent <name>` — optional. Defaults to `any`.
- `--source-note <path>` — optional. Applied to every spec.
- `--queue` — optional. Write to `tasks/queue/` instead of `tasks/`.
- `--dry-run` — optional. Print what would be created without writing files.
- `--skip-validation` — optional. Skip the bulk validation pass.
- `--validate-opts <opts>` — optional. Pass extra flags to the validator (e.g. `--skip-touches-paths`).

### After generation

1. **Fill each stub** — edit titles, `why`, `goal`, `touches_paths`, evals, anti-patterns, do-not-touch.
2. **Run bulk validation** — the script validates each file by default; failures are reported per-task.
3. **Commit** — `git add tasks/ tasks/_state.yaml tasks/_metrics.jsonl`

### Anti-pattern: silent skipping

Don't skip Phase 2 or Phase 4 silently. The `--fast` path is an **explicit opt-in**
(via `--intent-file` + known-domain context). If you're unsure, run the full
workflow on one spec first, then batch the rest once the pattern is proven.

---

## Decomposition (intent → atoms)

When the input is too big for one atomic spec — a PRD, a design doc, a fuzzy
intent, or "a set of calls" — **decompose it** into N linked atoms before
authoring. The converged shape is a **flat parent index of stubs + per-task
detail specs** (not a tree): `task-architect` finds the atoms, you wire the
`depends_on:` edges and the `parent:` field, and `batch-generate.sh` makes the
detail stubs (this is fan-out *into* Batch Sprint Compose, not a replacement).

**Holes are first-class blockers.** An unresolved open question is not a footnote:
an atom with an open hole is NOT safe-to-delegate. Encode the hole as
`status: blocked` + `blocked_reason:` (the validator maps `blocked` → A2A
`input-required` via `ts_a2a_state()`) plus a non-`(none)` `## Open Questions`
zone. A `blocked` atom is not `ready`, so it never reaches the safe-to-delegate
gate until the question is answered and it transitions to `ready`.

**Quiz the user before generating stubs.** Present the proposed breakdown as a
numbered list — per atom: title, `depends_on` edges, and what it delivers
end-to-end — and ask three things: does the granularity feel right (too
coarse / too fine)? are the edges correct (each atom depends only on atoms
that genuinely gate it)? should any be merged or split? Iterate until approved,
*then* run `batch-generate.sh`. Regenerating stubs is cheap; re-cutting a
half-built backlog is not.

**Wide refactors are the exception to vertical slicing.** A **wide refactor**
is one mechanical change — rename a column, retype a shared symbol — whose
blast radius fans across the whole codebase, so no vertical slice can land
green on its own. Don't force it into a tracer bullet; sequence it as
**expand–contract** atoms:

1. **Expand** — add the new form beside the old so nothing breaks (one atom).
2. **Migrate** — move call sites over in batches sized by blast radius (per
   package, per directory), each batch its own atom with `depends_on: [expand]`,
   staying green because the old form still exists.
3. **Contract** — delete the old form once no caller remains (one atom,
   `depends_on` every migrate batch).

Each atom still carries its own eval; the shape of the cut is what changes.

See [runbooks/decomposing-intent.md](runbooks/decomposing-intent.md) for the
step-by-step method and [concepts/decomposition.md](concepts/decomposition.md)
for the concept.

---

## Self-containment

The engine is portable as a single repo:

```bash
git clone https://github.com/luanmorenommaciel/task-spec.git
ln -s "$PWD/task-spec/bin/taskspec" /usr/local/bin/taskspec
# optional: bash task-spec/src/lib/install.sh --target /path/to/repo
# taskspec now works in EVERY repo on that machine
```

**Bash portability:** The core gate path — `validate-task-spec.sh`,
`safe-to-delegate.sh`, `run-task-spec.sh`, and `_lib.sh` (under `src/gate/` +
`src/lib/`) — is bash-3.2-safe and runs on the macOS system `/bin/bash`
(3.2.57) with no extra setup. Two auxiliary scripts, `lint-backlog.sh` and
`query-metrics.sh` (`src/backlog/`), use associative arrays (`declare -A`) and
so require **bash 4+**. They guard themselves via `ts_require_bash4`: if
launched under bash 3.x they auto-detect a bash 4+ on `PATH` and re-exec under
it, and if none is found they print a one-line remediation (`brew install
bash`) and exit 3 — never the cryptic `declare: -A: invalid option` failure.

External dependencies: Context7, Exa, Ref MCPs must be user-configured.

---

## Worker layer (MCPs)

| MCP | Purpose |
|-----|---------|
| Context7 | Fresh library/framework docs |
| Exa | Production examples and patterns |
| Ref | Canonical references |

---

## Specialist agent

Spawns **`task-architect`** for the judgment-heavy work:
- Lives at: `~/.claude/agents/task-architect.md`
- Installed via: `bash src/lib/install.sh`
- Runs in: isolated context, returns structured build plan
- Scoped tools: Read, Grep, Glob, Bash, Write, TodoWrite, MCP suite

---

## Threshold Mapping (severity-scaled)

Task quality threshold scales with consequence. Below the severity-specific
threshold, the agent ASKs the user before composing. Above it, the agent
PROCEEDS with a disclaimer.

| Severity | Threshold | Rationale |
|----------|----------:|-----------|
| cosmetic | 0.80 | Doc typos, comment fixes; cheap to revert |
| refactor | 0.85 | Code shape changes with tests; semantic equivalence required |
| feature | 0.90 | New behavior; well-scoped acceptance criteria |
| bugfix | 0.95 | Correctness change with regression risk (legacy default) |
| security | 0.98 | Authentication, auth, cryptography, secrets handling |
| financial-critical | 0.99 | Money fields, accounting, ledger; silent errors compound |

**Backward compatibility:** Tasks without a `severity` field default to `bugfix`
(0.95), preserving the historical IMPORTANT threshold.

| Action | Class |
|--------|-------|
| Reading the user's intent | ADVISORY |
| MCP research | STANDARD |
| Drafting evals | IMPORTANT (severity-scaled) |
| Refusing direct dispatch of XL/XXL nodes, or L on an ineligible backend | CRITICAL |
| Detecting subjective output | CRITICAL (refuses EDD, routes to SDD) |

---

## CLI commands (bundled under src/, dispatched by bin/taskspec)

| Command | Purpose |
|---------|---------|
| `generate-task-spec.sh <slug> <effort> [agent] [source]` | Create a new T-*.md from template |
| `batch-generate.sh --intent-file <path> --effort S|M [opts]` | Bulk-create N stub T-*.md files from an intent list, then bulk-validate |
| `validate-task-spec.sh [opts] <path>` | Lint a T-*.md against the current v3 format (legacy v0/v1/v2 accepted with warnings). Flags: `--shellcheck-evals`, `--dry-run-eval`, `--skip-touches-paths`, `--strict-depends`. `--emit-schema {frontmatter\|agent-contract}` prints the published JSON Schema (Draft 2020-12) and exits |
| `lint-backlog.sh [--help]` | Cross-task linter: detects touches_paths overlaps, depends_on cycles, duplicate IDs, stale preconditions across the backlog |
| `run-task-spec.sh [--ci] <path>` | Execute evals from a T-*.md. Runs each `eval_N` in isolation, then the Exit Check. `--ci` emits JSON-per-eval |
| `safe-to-delegate.sh [--stamp] [--skip-touches-paths] <path>` | **PRE-delegation gate.** Structural validate + shellcheck-evals + eval execution (broken-logic guard). Emits DELEGATE / DO-NOT-DELEGATE (exit 0/1). Asks "are the evals well-formed enough to delegate?" — assertion failure is EXPECTED for unbuilt work. |
| `accept-task.sh --handoff <file> [--stamp] [--gold-sanity] <path>` | **POST-execution gate.** Re-runs evals, verifies HMAC v3/TaskRevision, dependency closure, immutable Git base, committed+index+worktree+untracked blast radius, and required receipt policy. On `--stamp`, writes `AcceptanceRecord/v1` and the complete acceptance envelope atomically. `--no-blast-radius`, a missing key, a narrow signature, or a legacy receipt forces explicit supervised Tier 2. `--gold-sanity` blocks non-discriminating evals that also pass on the unpatched baseline. |
| `conformance-check.sh --level L0\|L1\|L2 --executor "<cmd>"` | **Executor conformance suite (v3).** Certifies that a CONSUMER honors the contract (reads format + runs evals / lifecycle / budget+park). `--self-test` runs the bundled `ref-executor.sh`. Makes "any conformant executor can pick it up" testable. |
| `ref-executor.sh <path>` | The canonical L2-conformant reference EXECUTOR (~60 lines). Not an AI agent — the worked example of the consumer contract (acquire lock → iterate within budget → done/park) for adapter authors. |
| `migrate-legacy-task.sh <path>` | Convert a legacy task's markdown checklist into v2.1 eval stubs + validation_card |
| `transition-status.sh <id> <new-status> [reason]` | Atomic status change |
| `rebuild-state.sh` | Regenerate `_state.yaml` from frontmatter (recovery). Run after direct writes or when state is stale. |
| `list-ready.sh [--effort=S] [--agent=any]` | Show tasks ready for pickup |
| `archive.sh` | Move done/parked tasks to subdirs |
| `backup-backlog.sh [dir]` | Snapshot tasks/ folder |
| `install-hooks.sh` | Install git pre-commit hook that runs `rebuild-state.sh` to catch drift from direct-Write users |
| `install.sh` | Install bundled agent to ~/.claude/agents/ |

---

## Linting

Task-Spec v3 files use YAML frontmatter with a `title:` field **and** a body H1 (`# Title`). This is intentional: the frontmatter title is machine-readable metadata; the body H1 is human-readable when the file is rendered outside a parser. The combination triggers **MD025** (multiple H1 headings) in markdownlint by default.

This skill ships a scoped `.markdownlintrc` in its root that tells markdownlint to treat the frontmatter `title:` as the document's sole H1:

```json
{
  "MD025": {
    "front_matter_title": ""
  }
}
```

The empty string `""` matches the frontmatter key name exactly, so the body H1 is no longer flagged as a duplicate.

**How to use:**
- If your IDE or linter looks at the skill root, no action needed.
- If your IDE lints from `tasks/` or the repo root, copy or symlink the config:
  ```bash
  # ship your own .markdownlintrc at tasks/ (see the template in this doc)
  ```

**Why not drop the body H1?** Because it breaks every existing spec and reduces readability for humans skimming raw markdown. The skill owns its convention via config rather than changing the convention.

---

## References

- `../spec/task-spec-v3.md` — the published format-v3 specification and compatibility history
- `concepts/eval-driven-development.md` — EDD methodology
- `concepts/edd-vs-sdd-honest-comparison.md` — when to use which
- `concepts/six-zones.md` — zone-by-zone deep dive
- `concepts/profiles.md` — **v3** effort-scaled profiles (lite/standard/full) + the behavior↔eval traceability rule
- `concepts/conformance-levels.md` — **v3** executor conformance L0/L1/L2 + the A2A lifecycle mapping
- `concepts/effort-gate.md` — XS/S/M/L leaves, XL/XXL nodes, and capability-based L routing
- `concepts/agent-contract.md` — cross-vendor contract (includes the generic `backend_metadata` field; the backend names itself)
- `concepts/decomposition.md` — **v3** intent/PRD → N atomic specs (flat index + detail atoms, holes-as-blockers)
- `concepts/backlog-architecture.md` — 5-layer state management
- `../spec/schemas/` — published Task-Spec, TaskPlan, TaskHandoff, AuthoringEvidence, and agent-contract schemas
- `patterns/runnable-bash-evals.md` — eval writing patterns
- `patterns/validation-card-yaml.md` — YAML contract patterns
- `patterns/atomic-status-transitions.md` — transition protocol
- `patterns/anti-patterns-extraction.md` — mining from MCP research
- `patterns/do-not-touch-detection.md` — repo-scan patterns
- `runbooks/from-fuzzy-intent.md` — paragraph → Task-Spec
- `runbooks/decomposing-intent.md` — **v3** intent/PRD/set-of-calls → N linked atomic specs
- `runbooks/from-meeting-note.md` — Krisp output → Task-Spec
- `runbooks/from-existing-task.md` — legacy task → v2.1 conversion
- `runbooks/batch-sprint-compose.md` — bulk intent list → N Task-Spec stubs
- `runbooks/validating-a-task-spec.md` — linting walkthrough
- `runbooks/recovering-from-crash.md` — state recovery
- `runbooks/empirical-experiment-protocol.md` — SDD vs EDD test design

---

## Remember

> **"Specs that verify themselves keep humans at the edges of the loop — at
> intent-setting and acceptance review — not in the middle of every iteration."**

**Mission:** Be the cornerstone primitive — the open, atomic, vendor-neutral,
self-verifying unit-of-work format that any conformant agentic system can produce,
consume, and trust. Humans enter at intent and at acceptance review; the execution
loop in between runs without them.

> **On trust:** the HMAC sign-off envelope is **tamper-evident, not tamper-proof**
> — it proves a spec's evals were not edited after the gate stamped them, with a
> repo-shared key. It is a drift/accidental-edit guard, not a security boundary.
> "Humans at intent + review" is the honest claim; "no humans" is not.
