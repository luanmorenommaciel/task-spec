# Changelog

All notable changes to the **task-spec** engine are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Version numbers follow
[Semantic Versioning](https://semver.org/) where MAJOR is the spec format version,
MINOR is additive format/feature changes, and PATCH is bug fixes / doc clarifications.

The canonical version lives in `./VERSION` and is mirrored by
`src/lib/_lib.sh` (`TASKSPEC_VERSION`), `integrations/claude-code/plugin.json`, and
`integrations/claude-code/marketplace.json`. The doc-consistency lint
(`tests/lint-skill-docs.sh`) asserts VERSION == the latest heading below == _lib.sh.

---

## [3.8.0] — 2026-08-13

The **revision-bound trust, graph, recovery, and DX** release. Format v3 remains
the authoring default, format v4 remains opt-in, and formats v1-v4 stay readable.

### Security and acceptance

- Added canonical `TaskRevision/v1` and `TaskAuthorization/v3`. The authority
  manifest excludes only named mutable operational fields, so unknown future
  fields are sealed by default. New stamps write `hmac-sha256-v3`; valid v1/v2
  seals remain authentic-but-narrow Tier 2 evidence.
- Added `TaskHandoff/v3`, UUID attempts, immutable base commits, dependency
  closures, non-clobbering `--out`, and v1/v2 compatibility writers behind an
  explicit flag.
- Added `ReceiptSubject/v1`, v2 evaluation/environment/graded/human/engine
  receipts, scoped `EvaluatorTrust/v1`, ordering/replay protection, and optional
  Ed25519 receipt signing.
- Hardened acceptance against committed, staged, unstaged, untracked, rebased,
  traversal, `.git`, and symlink-escaped changes. Tier-2 acceptance now requires
  explicit supervision flags.
- Added atomic `AcceptanceRecord/v1`, complete acceptance envelopes, idempotent
  attempts/metrics, crash recovery, and stable `AcceptanceFailure/v1` codes.
- Added `AcceptanceFinalized/v1` for successful JSON-mode acceptance so external
  schedulers can bind the exact record path and digest without parsing prose.
- Acceptance retries now reject changes to acceptor, tier, receipt set,
  supervision, or verifier identity. Status, backlog doctor, and transition-to-
  done verify the record subject and envelope rather than trusting its hash alone.

### Graph, recovery, and developer experience

- Added approved `TaskPlan/v1` materialization receipts with exact plan and task
  digests. Exact batch reruns are unchanged, while partial or conflicting
  output sets fail closed and individual file writes replace atomically.
- Added one deterministic stdlib resolver for `TaskGraphView/v1`, dependency
  closure, cycles, dangling edges, composition, supersession, write conflicts,
  ready frontier, blocked reasons, and concurrency groups.
- The resolver scans nested lifecycle buckets recursively. Leaf closures include
  only transitive task dependencies and containing composition ancestors, while
  handoff and acceptance reject conflicts with currently in-progress work.
- Added `taskspec graph`, `taskspec status`, and `taskspec doctor --backlog`.
  Markdown Task-Specs and Git remain canonical; graph and state are projections.
- Made frontmatter mutations atomic under the portable mkdir lock, moved the
  reference executor to lifecycle transition commands, enforced retry policy
  within signed budgets, and added no-progress circuit breaking.
- Deprecated advisory `blocks`; `depends_on` is authoritative. Explicit
  `supersedes` never rewrites downstream dependencies automatically.
- Added uniform per-command help, usage exit code 2, standard-library schema
  reference/fixture checks, locked migration/archive/state rebuilds, authoring-
  evidence age reporting, and integrity digests over optional A2A/MCP handoffs.
- Added an explicit `install.sh --global` user-level door for equivalent Codex/
  Kimi, Claude Code, and Grok Build skill copies plus the pinned CLI. The
  compatibility agent and host guidance now describe the same 3.8 lifecycle as
  the canonical skill, and the clean-room suite proves the global layout.

### Experimental opt-in extensions

- Added sealed authoring `evidence_refs` restricted to context/constraint/risk,
  provider smoke graduation, holdout expiry/rotation metadata, repeated eval
  audits, mutation-pack scaffolding, A2A v1.0 negotiation, and DSSE export for
  v2 receipts. These remain optional and do not authorize or accept work.
- Added validated experimental mutation manifest shapes for Python, JavaScript,
  Go, and Bash; repository-specific patches remain opt-in falsifiers.

### Compatibility and boundaries

- No format-v5 bump. MCP/A2A/DSSE remain optional adapters, not normative core
  dependencies. No scheduler, fleet, hosted dispatcher, silent replanner, or
  canonical graph database was added.
- The new adversarial suite covers downgrade, authority deletion, unknown-field
  expansion, replay, stale receipts, committed scope breaches, symlink escape,
  history divergence, closure drift, and interrupted acceptance recovery.

## [3.7.0] — 2026-08-12

The **evidence, integrity, and portability** release. Existing format-v3 tasks
keep their behavior; authors opt into format v4 explicitly.

### Added

- `taskspec demo`, a disposable install-to-accept proof that exercises planning,
  generation, DoD, Tier-1 authorization, handoff, eval execution, and
  independent acceptance without touching the caller's repository; plus a
  tagged-release workflow for the real curl and npm/GitHub distribution doors.
- Format-v4 `evaluation_policy` covering deterministic, private holdout,
  independently graded, and accountable human evidence. Required receipts are
  bound to the task authorization and block POST acceptance when missing,
  failed, or mismatched.
- `HoldoutBundle/v1` and executor-safe `HoldoutDescriptor/v1`, with digest/HMAC
  verification and `EvaluationReceipt/v1`. Private commands never enter
  `TaskHandoff/v2`.
- `EnvironmentContract/v1`, environment/graded/human/engine receipts, optional
  Ed25519 `AuthorizationReceipt/v1`, and explicit key revocation.
- `taskspec eval-audit` for current-pass plus baseline/mutation-fail evidence;
  `author-doctor` for authoring weaknesses; typed receipt validation that
  rejects credential-bearing keys.
- `TaskHandoff/v2` for v4, plus identity-preserving A2A/MCP envelopes, a
  read-only stdio MCP server, and a nine-family engine evidence matrix.
- Conformance C18 and a 28-check end-to-end v4 suite covering explicit authoring, isolated engine runs, fail-closed acceptance,
  receipt binding, holdout tampering, identity revocation, interoperability,
  and honest `unavailable` external-engine states.

### Compatibility and boundaries

- `taskspec new` still authors format v3 by default; `--format 4` is opt-in.
- Format v3 requires no v4 receipt and its existing gates remain unchanged.
- The release does not claim real-model runs, production sandbox enforcement,
  fleet scheduling, deployment proof, or A2A/MCP certification. The checked-in
  nine-family matrix is a reproducible template whose entries remain disabled
  until actual runs are retained.
- Pinned curl and npm/GitHub installation remain pending until the `v3.7.0` tag
  exists and the release-install smoke workflow retains successful results.

## [3.6.0] — 2026-08-11

The **canonical atomic-task experience** release. Format v3 remains current and
the CLI, skill, and installation surfaces become portable across coding harnesses.

### Added

- `taskspec init`, idempotent `taskspec setup signing`, and a readiness board
  with one exact next action.
- `TaskPlan/v1` preview and approved generation, `taskspec dod`, read-only
  `TaskHandoff/v1`, `taskspec agent-context`, completion, global `--json` and
  `--dry-run`, plus `NO_COLOR` / `TASKSPEC_COLOR` behavior.
- Equivalent Codex/Kimi, Claude Code, and Grok Build skill installation; pinned
  copy and checkout-symlink modes; npm/GitHub and Claude marketplace metadata.
- Non-normative Firecrawl, Tavily, and Exa packs sharing
  `AuthoringEvidence/v1`. Only offline fake adapters are supported in CI; no
  live-provider claim is made.
- TaskPlan, TaskHandoff, and AuthoringEvidence schemas and an end-to-end docs
  structure.

## [3.5.0] — 2026-08-11

The **engine parity** release, ported from the immutable
`converge@f78f077` donor baseline into the standalone canonical layout.

### Added and changed

- Six-tier sizing: XS/S/M/L leaves and XL/XXL nodes, configurable L backends,
  write-surface budgets over `touches_paths ∪ creates_paths`, and node rules.
- HMAC envelope v2 seals authorization fields. Valid v1 seals remain readable
  as supervised Tier 2 and can be intentionally re-stamped.
- Worktree-common keys, task-workspace evals, stub resistance,
  `validate --no-state`, deterministic state refresh, dependency-aware
  readiness, collision/concurrency analysis, safe rendering/metrics,
  `tracker_ref`, Definition of Done, and TaskPlan preview foundations.
- Portable settlement: `status: done` requires `accepted: true`; Converge-only
  receipt enforcement is not part of core.

### Compatibility

- `format_version` remains `3`; v0/v1/v2/v3 remain on the documented read path.
  `linear_ref` remains a deprecated compatibility alias of `tracker_ref`.

## [3.4.1] — 2026-08-03

The **first-CI-run hardening patch** (PATCH — no format change;
`format_version: 3` unchanged). The brand-new CI did exactly what it was built
for and caught a real bash-3.2 engine bug plus two environment gaps on its
first two runs.

### Fixed

- **bash-3.2 crash in `safe-to-delegate.sh` (pre-existing; caught by the new
  macOS CI leg).** Line 99 expanded `"${PASS_THROUGH[@]}"` — an empty array in
  the common no-passthrough case — under `set -u`, which is a hard
  "unbound variable" error on macOS system bash 3.2 but silently fine on
  bash 4+. The gate died before validating or stamping, breaking
  `taskspec gate` on the documented bash-3.2 floor. Fixed with the portable
  `${PASS_THROUGH[@]+"${PASS_THROUGH[@]}"}` idiom; every other array expansion
  in `src/` was audited and is already guarded by a `${#arr[@]} -gt 0` check.
  Local runs had masked this because Homebrew bash 5 shadows `/bin/bash` in a
  dev PATH; the macOS CI leg exercises the real 3.2 floor (verified locally
  with a bash→/bin/bash PATH shim: full suite green).
- **`taskspec doctor` shellcheck guidance corrected.** It claimed the gate
  "skips the shellcheck-evals lint" when shellcheck is missing; in fact
  `safe-to-delegate.sh` always passes `--shellcheck-evals` and the validator
  hard-errors without the binary. The WARN now says the gate will FAIL.
  README Install requirements list `shellcheck` accordingly.
- **CI environment gaps.** The macOS leg installs shellcheck v0.10.0 from the
  upstream release (SHA-256-verified per arch — ubuntu images ship it), and
  both legs install pinned `pyyaml==6.0.2` for the schema-fidelity step of
  `test-portability-e2e.sh`.

---

## [3.4.0] — 2026-08-03

The **presentation & verification-surface** release (MINOR — repo polish only;
no format change, `format_version: 3` unchanged, no engine behavior change,
every v3.3.0 spec validates identically). Brings the public surface to the
standard of a shipped open-source product: brand identity, a README that reads
like a spec, a single `make check` release gate, linted docs, and
credential-free CI.

### Added

- **Brand identity (`assets/`).** A strict shared palette (near-black `#0a0f14`,
  eval-green `#3ddc97`, seal-amber `#ffb454`, fail-red `#ff5d73`, contract-cyan
  `#5cc8ff`, muted slate `#8ba3b5`) across: `taskspec-banner.png` (README hero,
  2:1 social-preview size, generated from the hand-authored
  `taskspec-banner.svg` source), `taskspec-mark.svg` (256×256 page-and-seal app
  mark), `taskspec-logo.svg` (wordmark lockup), and `taskspec-hero.svg` (the
  closed-loop diagram with fail-closed routes). All SVGs carry `role="img"` +
  `<title>`/`<desc>` accessibility tags.
- **README overhaul.** Centered hero (banner + caption + tagline "**Write it.
  Seal it. Prove it.**"), brand-colored shields linking in-repo plus a CI badge,
  anchor nav, the closed-loop hero SVG with a `<details>` Mermaid fallback
  (palette-matched `classDef`), a CLI map, a `## Verified surface` section
  documenting `make check` + CI, and the honest boundary converted to a
  claim/truth table with explicit non-claims (no Homebrew/curl installer, real-
  engine CI still landing).
- **`Makefile` — the single release gate.** `make check` = `taskspec doctor` +
  both lints + every `tests/test-*.sh` + the conformance suite + the CLI
  self-test; prints `CHECK=READY`. Mirrors the AGENTS.md verification list.
- **`tests/lint-docs.sh` — markdown hygiene lint.** Local relative links/images
  resolve to existing files (anchors stripped, `%20` decoded, `node_modules`
  excluded) and code fences are balanced, across README/AGENTS/TODO + `docs/`,
  `adapters/`, `agents/`, `integrations/`, `spec/`. Wired into `make check`.
- **Credential-free CI (`.github/workflows/ci.yml`).** One job, matrix
  `ubuntu-latest` + `macos-latest`, runs exactly `make check` — CI runs the same
  boundary a contributor runs locally. Hardened: `permissions: contents: read`,
  `persist-credentials: false`, actions pinned by SHA, concurrency
  cancel-in-progress, 20-minute timeout. `.github/dependabot.yml` tracks the
  actions ecosystem weekly.

### Changed

- **`TODO.md` P0-1 annotated** — the credential-free CI foundation and README
  badge now exist; the real-engine matrix (Claude/Codex executors in CI) remains
  the open work.
- **`AGENTS.md`** — `make check` documented as the one-command gate; the docs
  lint added to the test list.

---

## [Unreleased: extraction note]

### Changed

- **Extracted from `converge/skills/task-spec` at v3.3.0 into this standalone engine
  repo.** The skill is now a vendor-neutral engine with its own home: the format spec
  moved to `spec/task-spec-v3.md` (the old `references/concepts/task-spec-v1.md`
  filename is retired), JSON Schemas to `spec/schemas/`, the conformance suite to
  `spec/conformance/`, and the flat `scripts/` directory to `src/<verb>/`
  (author / gate / accept / backlog / dispatch / lib). The `bin/taskspec` CLI is the
  new canonical, stable agent-facing surface; the Claude Code skill is now a thin
  delegating layer under `integrations/claude-code/`. No format change:
  `format_version: 3` unchanged, every v3.3.0 spec validates identically.

---

## [3.3.0] — 2026-07-17

The **decomposition shape** release (MINOR — additive guidance; `format_version: 3`
unchanged, every existing spec validates identically). Field-tested patterns from
external best-of-breed skills, absorbed into the authoring workflow.

### Added

- **Vertical-slice rule ("cut tracer bullets, not layers").** Feature atoms prefer a
  narrow but complete path through every layer over a horizontal slice of one layer —
  the eval defines *done*, the vertical cut defines *worth doing alone*.
- **Context-window sizing ceiling.** An atom must fit — spec, cited ADRs, touched
  files, working diff — in one fresh executor session; if not, split and wire
  `depends_on`.
- **Breakdown quiz before stub generation.** Present the proposed atoms (title,
  edges, end-to-end deliverable) and confirm granularity/edges/merges with the user
  BEFORE `batch-generate.sh` — regenerating stubs is cheap, re-cutting a half-built
  backlog is not.
- **Expand–contract sequencing for wide refactors.** Mechanical whole-codebase
  changes (rename, retype) are cut as expand → migrate-in-batches → contract atoms
  instead of being forced into a tracer bullet.

---

## [3.2.0] — 2026-07-06

The **size-aware routing** release (MINOR — additive; `format_version: 3` unchanged, every
existing spec validates identically). Turns the effort field into an engine-aware dispatch
signal and completes the "atomic, engine-agnostic task creator" thesis.

### Added

- **Size → engine recommendation.** The effort gate now maps t-shirt size to a recommended
  builder: `XS/S/M → Kimi` (sprinter, atomic cranks), `L → GLM` (marathoner, long-horizon),
  `XL → SDD` (route out). The recommendation is **advisory** — a dispatcher heuristic keyed
  off `effort`, expressed in `runbooks/dispatching-a-task-spec.md`. It never overrides an
  author's explicit `execution_backend` and keeps the agent-contract C9 black-box guarantee
  intact (see `references/concepts/agent-contract.md`).
- **New `Size → engine recommendation` table** in the dispatch runbook.

### Changed

- **Effort gate is now size-tiered and engine-aware** (`scripts/validate-task-spec.sh`,
  `references/concepts/effort-gate.md`):
  - `XS/S/M` — accepted (unchanged behavior; XS was previously an undocumented enum value,
    now defined: ≤ 2 hours, trivial one-liner).
  - `L` — **newly accepted, but ONLY with `execution_backend: glm`**, and only if it carries
    ONE coherent machine-checkable done-condition. An L spec on any other backend is a hard
    error → decompose into S/M atoms (which recommend GLM) or route to SDD. The relaxation is
    narrow and loud (a validator WARNING is emitted on every accepted L spec).
  - `XL` — rejected → route to **SDD**. The escalation target is broadened from AgentSpec-only
    to a menu: **AgentSpec / OpenSpec / SpecKit**. XL is the top t-shirt tier ("XXL" and larger
    live here in prose).
- **`execution_backend` examples** trimmed to the current fleet: `any, claude, codex, kimi,
  glm, gemini` (dropped `cursor, agentspec, anthive, taskship` from the non-normative example
  list — the field remains an OPEN STRING, so those still validate).
- **Dispatch runbook** engine table refreshed: added `glm`, removed `taskship`/`anthive` rows,
  and reframed each engine by fleet role (Claude orchestrates · Codex reviews · Kimi/GLM build).

### Rationale

L is the one tier where relaxing atomicity is defensible: a 3–7 day task can occasionally
have a single coherent done-condition that a 1M-context, long-horizon engine (GLM) sustains
across hundreds of tool-call rounds — a capability the sprinter class does not have. Gating L
to `glm` makes the relaxation earn its keep rather than opening the gate for every backend.
Everything at XL and beyond stays out of Task-Spec by design: the spec phase itself is the
work, which is what SDD is for.

## [3.1.1] — 2026-07-01

The **Anthropic-conformance patch** (PATCH — no format change; `format_version: 3`
unchanged, a v3.1.0 spec validates identically). Brings the skill's own frontmatter into
compliance with Anthropic's official Skill validator (`skill-creator/scripts/quick_validate.py`)
without touching a single crown-jewel mechanic.

### Changed

- **`version` moved from the frontmatter top level into `metadata.version`.** Anthropic's
  skill spec forbids a top-level `version` key (allowed: name, description, license,
  allowed-tools, metadata, compatibility). The canonical value is unchanged (`3.1.0`); only
  its location in `SKILL.md` moved. `plugin.json`, `marketplace.json`, and
  `_lib.sh:TASKSPEC_VERSION` are untouched.
- **`scripts/lint-skill-docs.sh` (Check 2) now reads `metadata.version`** first, with a
  legacy top-level `version:` fallback, so the dogfood doc-consistency lint stays green.
- **Description arrow `↔` ASCII-ized to `behavior-to-eval`** — portability nicety; the
  validator permits the glyph (only `<`/`>` are banned), but ASCII travels everywhere.

### Not changed (the crown jewels — preserved exactly)

The 6 zones, the 9-phase closed loop (validate → safe-to-delegate → accept), the
behavior-to-eval traceability lint, the HMAC sign-off envelope + 3-tier policy,
`accept-task.sh` GATES A–E (incl. `--gold-sanity` Goodhart guard), the effort gate,
conformance levels L0/L1/L2, the open-string `execution_backend`, the 5-layer backlog
architecture, and every bundled script and concept doc are byte-for-byte unchanged.

---

## [3.1.0] — 2026-06-18

The **open-standard hardening release** (MINOR — `format_version: 3`, additive). Builds on
the v3.0.0 closed loop with a published machine schema, a generic backend-metadata field,
two opt-in acceptance gates that defend against 2026-era reward-hacking, the canonical A2A
v1.0 TaskState dispatcher, DAG cycle detection in the cross-task linter, and a decomposition
path from intent to N atomic specs. Backward-compatible: a v3.0.0 spec validates unchanged.

### Added

- **Post-execution `--gold-sanity` gate (accept-task.sh GATE E)** — the Goodhart-guard
  upgrade. BLOCKS a non-discriminating eval set (one that passes even on the UNPATCHED
  baseline) by reconstructing the baseline in an ephemeral git worktree at `--base` /
  frontmatter `baseline_ref:` / `reference_solution:`, running the current spec's evals there
  (must FAIL) and on the current state (must PASS). Degrades to a warn when git/baseline is
  unavailable. Off by default. See `scripts/accept-task.sh`.
- **`requires:` isolation block + acceptance GATE D** — an OPTIONAL frontmatter object
  (`base_image` / `deps` / `network`) declaring what the executor's sandbox must provide.
  `accept-task.sh` reports it (document-and-warn — the bash tool cannot enforce egress) and
  WARNS when a `full`-profile spec leaves `requires.network` unset. New `ts_has_requires` /
  `ts_requires_field` helpers in `_lib.sh`.
- **A2A v1.0 TaskState dispatcher (`ts_a2a_state_v1` in `_lib.sh`)** — emits the canonical
  `TASK_STATE_*`-prefixed members (`TASK_STATE_SUBMITTED|WORKING|INPUT_REQUIRED|COMPLETED|
  FAILED`, catch-all `TASK_STATE_UNSPECIFIED`). The v3.0.0 `ts_a2a_state` is retained as the
  stable lowercase legacy alias.
- **`depends_on` DAG cycle detection (lint-backlog.sh)** — the cross-task linter now detects
  `depends_on` cycles via `tsort` (with a pure-bash DFS fallback) and reports the involved
  nodes, alongside the existing dangling-edge (non-existent task) check.
- **Decomposition runbook + concept doc** — `runbooks/decomposing-intent.md` and
  `references/concepts/decomposition.md`: intent / PRD / set-of-calls → N linked atomic specs
  (flat parent index of stubs + per-task detail specs, `depends_on`/`parent` edges,
  holes-as-blockers via `status: blocked`).
- **Published JSON Schema (Draft 2020-12)** surfaced as the format's machine contract:
  `validate-task-spec.sh --emit-schema {frontmatter|agent-contract}` is the single source of
  truth; the frontmatter schema now declares `profile`, `parent`, `accepted*`, `requires`,
  `baseline_ref`, and `reference_solution`.

### Changed

- **`backend_metadata` replaces the vendor-named `codex_metadata` / `kimi_metadata`
  fields** — a single generic, optional executor-specific key/value map (the backend names
  itself). Reflected in `templates/task-spec.md.tpl`, `references/schemas/agent-contract.schema.json`,
  and `references/concepts/agent-contract.md`. Vendor neutrality at the field level.
- **`execution_backend` documented as an OPEN STRING in the schema** — the frontmatter
  schema lists `examples` (non-normative), not an `enum` allow-list; the dispatch table in
  `SKILL.md` now routes to the non-normative `runbooks/dispatch-recipes/` adapters instead of
  enumerating vendors as if normative.

### Migration

No action required — v3.0.0 specs validate unchanged. To adopt the new gates, add
`baseline_ref:` (or pass `--base`) and run `accept-task.sh --gold-sanity`, and/or add a
`requires:` block. Rename any `codex_metadata:` / `kimi_metadata:` to `backend_metadata:`.

---

## [3.0.0] — 2026-06-18

The **open-format / closed-loop release** (MAJOR — `format_version: 3`, additive).
Twelve coordinated changes turn Task-Spec into a vendor-neutral open format with a
verified consumer contract and a closed author→gate→dispatch→execute→**accept**
loop. Every change is backward-compatible: a v2.2 spec with no new fields validates
as `profile: standard`.

### Added

- **Effort-scaled profiles** (`profile: lite | standard | full`) — scales required
  zones to a task's blast radius without weakening the eval moat. Absent → standard.
  See `references/concepts/profiles.md`.
- **Behavior zone** (Given/When/Then, stable `B-N` ids) — the BDD layer between
  intent and evals; required for standard/full, optional for lite.
- **Behavior↔eval traceability lint** — every behavior must be verified by ≥1 eval
  (`verifies: [B-N]`) and every eval must map to a declared behavior. Bidirectional
  coverage enforced as a validator error. The chain that makes the spec machine-checked.
- **`accept-task.sh` — the POST-execution acceptance gate** (the headline component).
  Re-runs evals from a clean checkout (must PASS), checks the change set is within
  `touches_paths`/`do-not-touch` (blast-radius / Goodhart guard), and re-verifies the
  sign-off HMAC (eval bodies unchanged). Stamps `accepted: true`. Closes the loop.
- **Conformance levels L0/L1/L2 + `conformance-check.sh`** — certifies an EXECUTOR
  (not just a spec) honors the contract: reads-format+runs-evals / lifecycle / budget+park.
  Makes "any conformant executor can pick it up" testable. `--self-test` included.
- **`ref-executor.sh`** — the canonical L2-conformant reference executor (~60 lines):
  the worked example of the consumer contract for adapter authors.
- **`parent:` frontmatter** — references a FEATURE-altitude PRD/SDD; the task DISTILLS
  it, never embeds it (preserves atomicity).
- **A2A lifecycle mapping** — Task-Spec status ↔ A2A (Linux Foundation) `TaskState`
  (`ts_a2a_state` in `_lib.sh`); surfaced by the validator and conformance harness.
- **`ts_timeout` portable watchdog** in `_lib.sh` — `timeout`→`gtimeout`→pure-bash
  fallback (macOS ships no `timeout`).
- Concept docs: `profiles.md`, `conformance-levels.md`.

### Changed

- **`execution_backend` is now an OPEN STRING**, not a closed enum — names any
  executor; bundled dispatch recipes (`runbooks/dispatch-recipes/`) are the
  non-normative adapter layer. Vendor neutrality at the field level.
- **Claims hygiene** — the closing motto no longer says "no humans in the loop";
  the honest claim is humans at intent + acceptance review. The HMAC envelope is
  documented as tamper-EVIDENT (drift guard), not tamper-PROOF (security boundary).
- `agent_contract` v2 schema validation now applies to `format_version: 3` (the
  contract schema is unchanged; v3 is additive at the spec level).
- Acceptance envelope floor: `accepted: true` requires `accepted_by` + `accepted_at`
  and presupposes `signed_off: true` (rejects hand-stamping, mirrors the sign-off floor).

### Migration

No action required for existing specs — they validate as `profile: standard` with
`format_version` unchanged. To adopt v3 features, add `profile:` and a `## Behavior`
section, or regenerate with `generate-task-spec.sh --profile <lite|standard|full>`.

---

## [2.2.1] — 2026-06-03

The **eval-runner stdin-hang fix** (PATCH). Pushes the v2.2 format from the 9.0
sign-off to **9.5** by closing the last reachable robustness gap: the eval runner
could block forever waiting on stdin. Same format, harder substrate.

### Fixed

- **`scripts/run-task-spec.sh` — eval runner no longer hangs on stdin.** The
  per-eval invocation (`bash -c "source …; eval_N"`) inherited the gate-runner's
  stdin. An eval body containing `read` — or any construct that consumes stdin —
  would **block indefinitely** waiting for input that never arrives, hanging the
  whole gate (and any CI dispatch reading its JSON). Both the per-eval runner and
  the Exit Check runner now redirect stdin from `/dev/null`, giving immediate EOF.
  This is load-bearing: the new `B:reads-stdin` fuzz case provably HANGS (killed
  at the 8s timeout, RC=137) with the per-eval guard removed and completes
  cleanly with it. The Exit Check guard is defense-in-depth (a malformed Exit
  Check body fails at script-build time, not on a stdin read), kept for symmetry
  with the per-eval path.

### Changed

- **Removed dead `overall_pass` accumulator** from `run-task-spec.sh`. It was set
  on per-eval failure but never read — the final verdict is the Exit Check's exit
  code, per the `signed_off` contract. shellcheck SC2034 surfaced it; deleting the
  vestigial state is cleaner than annotating it.

### Added

- **`tests/test-extractor-fuzz.sh` — adversarial fuzz of the extract-and-run
  path** (19 cases). (A) extraction correctness on heredoc-heavy bodies (arith
  `<<`, delimiter literally `bash`, fake fences/headers inside heredocs, nested
  and quoted heredocs); (B) robustness invariant (never hang, never leak a raw
  bash/awk/sed error) including the load-bearing `reads-stdin` case; (C)
  defense-in-depth coverage of the Exit Check runner. Honors `--version` via
  `ts_version_flag` (doc-lint Check 4).

---

## [2.2] — 2026-06-02

The **key-optional HMAC sign-off envelope** release (B2). The crypto deferred in
v2.1.1 is now HERE. `safe-to-delegate.sh --stamp` seals a real HMAC-SHA256 over a
canonical payload; `validate-task-spec.sh` Check 17 recomputes and compares.
Sign-off is no longer trivially forgeable by hand-edit — closing the gap the
`T-20260603-fake-envelope.md` fixture documented.

### Added

- **`scripts/_lib.sh` crypto floor.** `ts_sha256` and `ts_hmac_sha256` detect a
  provider in priority order (openssl → `shasum -a 256` → `sha256sum`). When only
  a plain sha256 tool is present, HMAC is built manually via the RFC-2104
  ipad/opad construction (block size 64) — byte-for-byte identical to
  `openssl dgst -sha256 -hmac KEY`. When NONE of the three providers exists the
  helpers return a sentinel and the gate degrades to structural-only (Tier 2);
  a missing crypto binary NEVER produces a broken install or a hard error.
  Adds `ts_resolve_signing_key`, `ts_keyid`, `ts_spec_body`, `ts_body_digest`,
  `ts_signoff_payload`, `ts_compute_signoff_sig`.
- **`scripts/safe-to-delegate.sh --stamp` now seals `signed_off_sig`.** After
  writing the three plaintext `signed_off*` lines, it computes HMAC-SHA256 over a
  canonical fixed-field payload (`id`, `body_digest` = sha256 of the spec body
  after the closing frontmatter `---`, `signed_off`, `signed_off_by`,
  `signed_off_at`) and writes `signed_off_sig: hmac-sha256-v1:<keyid>:<hex>`. The
  signed set EXCLUDES the `signed_off_sig` line itself and is independent of
  frontmatter line ordering, so the MAC verifies on the very next read.
- **`scripts/validate-task-spec.sh` Check 17 three-tier degrade.** The structural
  floor is unchanged. When a key + sig are present the MAC is recomputed and
  compared. **Tier 1** (key + sig + MAC verifies) = full crypto trust, exit 0;
  **Tier 2** (no key, or sig absent = legacy spec) = structural-only with a loud
  warning, exit 0 (never hard-fails for a missing key); **Tier 3** (MAC mismatch
  or malformed sig) = hard FAIL exit 1, "DO NOT DELEGATE: spec body or envelope
  modified after stamping".
- **`configs/setup-taskspec-signing-key.sh`** generates a 256-bit key, writes it
  chmod-600 to `.git/info/taskspec-signing-key` (when `.git` is a real directory)
  or prints `TASKSPEC_SIGNING_KEY` instructions (worktree `.git` is a FILE), and
  prints the keyid. Stored OUTSIDE version control.
- **Key resolution** (`ts_resolve_signing_key`): env `TASKSPEC_SIGNING_KEY` (file
  path → read it; else raw key material), then `.git/info/taskspec-signing-key`
  only when `git rev-parse --git-dir` resolves to a real directory, then no key
  → Tier 2.
- **Tests & fixtures.** `tests/test-hmac-envelope.sh` (keyed Tier-1/2/3 suite +
  portability-floor masking + `.git/info` fallback), wired as
  `tests/test-task-spec-skill.sh --suite hmac`. New fixtures
  `T-20260603-stamp-then-verify.md` and `T-20260603-tampered-body.md` (keyed,
  excluded from the default no-key oracle so the existing 15 fixtures still
  behave as before).
- **Schema.** `references/schemas/task-spec-frontmatter.schema.json` now declares
  the real `signed_off_sig` contract (pattern `hmac-sha256-v1:<keyid>:<hex>`,
  what it covers, key-optional). The previously-dead `signed_off_envelope` object
  stub is re-described as reserved for a future per-author detached-signature
  upgrade.

### Changed

- **`references/concepts/signed-off.md`** rewritten: crypto is HERE now (not
  "planned for v2.2"). Honest IS/IS-NOT — HMAC is symmetric, so it binds "a
  repo-key holder stamped this", NOT per-author non-repudiation (an asymmetric
  Ed25519/DSSE upgrade is the named future hardening). Threat model = an
  adversarial co-author who read the skill, not a remote supply-chain attacker.
  Documents the three tiers and the Tier-2 supervised-only policy.
- **`runbooks/dispatching-a-task-spec.md`** adds the mandatory sign-off-tier gate:
  Tier 2 is read/inspect/triage only — NOT dispatch-eligible for unsupervised
  crank — closing the downgrade-bypass (run the verifier without the key to reach
  the forgeable Tier-2 state). `safe-to-delegate.sh` surfaces the tier in VERDICT.

### Security

- HMAC is symmetric: a repo-key holder can forge a Tier-1 stamp. The envelope
  defends against an adversarial co-author who hand-edits an envelope or a silent
  post-stamp edit — NOT against an attacker who already holds the key. Per-author
  non-repudiation is explicitly out of scope and deferred to a future asymmetric
  upgrade.

### Fixed (round-5 adversarial review)

- **Shell-injection in the crypto-sealing path (HIGH).** `safe-to-delegate.sh`
  wrote `signed_off_by` via a `sed s|…|${STAMP_BY}|` substitution. A `--stamp-by`
  / `$USER` value containing `|` silently FAILED to seal while the gate still
  printed "Tier 1 crypto trust" (the `sed … && mv` chain suppressed `set -e`); an
  `&` silently mis-attributed the sign-off WITH a valid seal. Fixed by routing
  every envelope field (including `signed_off_sig`) through one injection-safe
  primitive, `ts_set_frontmatter_field` in `_lib.sh`, which carries the value via
  `awk -v` (never a sed delimiter). The five adversarial inputs (`build|42`,
  `a&b`, `team/build`, a full `s|.*|INJECTED` payload, an embedded space) are now
  regression-locked in `test-hmac-envelope.sh` Scenario 7.
- **Conformance suite silently no-op'd on bash 3.2 (HIGH).**
  `tests/conformance/run_conformance.sh` discovered fixtures with `mapfile`
  (bash-4-only). On macOS system bash 3.2 it printed "mapfile: command not found",
  left the fixture array empty, and reported success while testing NOTHING.
  Rewritten as a bash-3.2-safe `while read` loop so the vendor-facing conformance
  gate runs on the portability floor; `test-bash-portability.sh` section (d) now
  asserts the runner + adapters carry no bash-4-only constructs.

### Changed (round-5 adversarial review)

- **Tier-2 "supervised-only" is now an enforced control, not just prose.**
  `safe-to-delegate.sh` emits a machine-readable `TIER=N` line for a signed spec,
  and a new `--require-tier1` flag makes the gate exit non-zero on anything below
  Tier 1 — so a CI dispatcher branching on `$?` cannot crank a Tier-2 spec
  unsupervised. Documented in `runbooks/dispatching-a-task-spec.md`; covered by
  `test-hmac-envelope.sh` Scenario 8.
- **Cross-engine equivalence proof strengthened (B3).** The Python-vs-TypeScript
  oracle compared `eval_count` (a number) and four scalars. It now compares the
  FULL ORDERED `eval_ids` list and a canonicalized `validation_card` projection
  (`agent_contract` zones, `retry_policy`, success-criteria), so two consumers
  that find the same COUNT of evals but disagree on WHICH evals now diverge.
- **Worktree key-path docstrings corrected.** `_lib.sh` and
  `setup-taskspec-signing-key.sh` wrongly implied a worktree's `.git` being a file
  skips the `.git/info` key path. `git rev-parse --git-dir` resolves to the
  per-worktree gitdir, so the key IS found there — the comments now describe the
  real behavior (proven by the `.git/info` fallback test running in this worktree).

### Fixed (round-6 re-review — hardening the round-5 fixes)

- **`ts_set_frontmatter_field` now rejects multi-line values.** A value containing
  a newline or CR is refused with a clear error (return 2) and the file is left
  untouched — closing a residual injection path (a multi-line scalar would inject
  an extra frontmatter line). Regression: `test-hmac-envelope.sh` S9.
- **`ts_set_frontmatter_field` now hard-fails on un-writable frontmatter.** A spec
  with no closing `---` previously left the field silently unwritten while
  returning 0; the caller would then HMAC a spec missing the field. The awk now
  signals "not written" (`END { if (done==0) exit 3 }`) and the function returns
  1 with a clear error; `safe-to-delegate.sh` BLOCKs rather than sealing a
  half-stamped spec. Regression: `test-hmac-envelope.sh` S9.
- **Cross-engine oracle now normalizes whole-number floats** (`30.0` → `30`) so a
  YAML numeric-typing difference between the Python and TypeScript parsers cannot
  produce a false divergence in `test-portability-e2e.sh` Step 7.

### Fixed (round-7 convergence review)

- **`awk -v` escape-expansion injection closed (HIGH).** Round-6 rejected literal
  newline BYTES, but `ts_set_frontmatter_field` still passed the value via
  `awk -v`, which runs C-escape processing — so the two characters backslash+n
  (no newline byte, so the round-6 guard let it through) were expanded by awk
  into a real newline, injecting a forged extra frontmatter line via `--stamp-by`.
  The value is now carried through the process environment (`ENVIRON[]`), which
  does NO escape processing: every byte (`|`, `&`, `\`, backslash-n, tab) is
  written verbatim as one scalar. The primitive's docstring "verbatim incl. `\`"
  guarantee is now true. Regression: `test-hmac-envelope.sh` S9 case (c).
- **Conformance results.json write now fails loud on bash 3.2 (LOW).** A redirect
  failure on the `{ … } > results.json` brace group does not trip `set -e` on
  bash 3.2, so an unwritable target produced a green run with a stale artifact.
  The write goes via a temp file whose presence + a regular-file check on the
  destination are verified explicitly; any failure is a `FATAL` exit 1.

### Fixed (round-8 convergence — temp-file symlink hardening)

- **Symlink-following on the predictable `.$$` temp-write path closed (LOW).** The
  in-place editors write to a predictable sibling temp (`<file>.fmset.$$` /
  `.tmp.$$`) then `mv` it over the original. A shell redirect `> "$tmp"` follows
  a pre-existing symlink, so an actor with write access to the directory could
  plant one to clobber an arbitrary target. New `ts_prepare_tmp` helper (`_lib.sh`)
  `rm -f`s the temp path before every redirect at all five sites
  (`ts_set_frontmatter_field`, `validate-task-spec.sh`, `transition-status.sh`,
  `rebuild-state.sh`, `run_conformance.sh`), so the redirect always creates a
  fresh regular file. Scoped LOW — the temp is a repo-internal sibling, not in
  world-writable `/tmp` — but closed for defense-in-depth. Regression:
  `test-hmac-envelope.sh` S9 case (d).

---

## [2.1.1] — 2026-06-02

The "shippable for any agent" hardening release. Closes the 8 bugs surfaced by
the round-2 adversarial review of v2.1 and ships the cross-engine artifacts
(JSON schemas, reference consumers in Python and TypeScript, per-engine
dispatch recipes, RFC-2119 contract + conformance fixtures) that turn the
"vendor-portable" claim from rhetoric into a testable spec.

### Retraction — "HMAC envelope" was misleading

The v2.1.0 entry below described the `signed_off` envelope check as an "HMAC
envelope." That naming was wrong and is **retracted**. The check is a
**structural sign-off envelope**: it asserts that `signed_off: true` is
accompanied by `signed_off_by` and `signed_off_at` lines populated by
`safe-to-delegate.sh --stamp`. It catches the dominant failure mode
(accidental hand-stamping) but does **not** provide cryptographic protection
against adversarial hand-stamping — anyone with write access to the file can
populate the three lines manually and bypass the check. The `tests/fixtures/
T-20260603-fake-envelope.md` fixture documents this limitation by example.
Real HMAC crypto (with key management + rotation) is deferred to v2.2; until
then, every doc, error message, and code comment that previously said "HMAC"
now says "structural sign-off envelope."

### Added

- **WS-A — P0 silent-failure patches (Bugs 1, 2, 5).** `validate-task-spec.sh`
  now uses safe-default capture (`${var:-}`) for the three `signed_off*`
  reads, so a missing `signed_off_by:` line under `signed_off:true` produces
  a loud `hand-stamping detected` error at exit 1 instead of a 0-byte
  silent abort under `set -euo pipefail`. `safe-to-delegate.sh --stamp`
  no longer silently no-ops when envelope lines are absent — it now
  appends missing `signed_off_by:` and `signed_off_at:` lines via an
  `awk`-based frontmatter injection before the closing `---`.
  `tests/test-task-spec-skill.sh` Step 1 was broken since v2.1's
  generator-output rename (looked for `>>> Created`, generator now prints
  `Spec written:`); fixed to the new contract and locked by a new
  `tests/test-generator-output-contract.sh` regression guard.
- **WS-B — Generic inverted-eval lint (Bugs 3, 4).** `validate-task-spec.sh`
  Check 16 collapses the per-command regex stack (`grep -c`, `wc`, etc.)
  into a single coherent rule: any `$(...)` or backtick substitution
  followed by `|| (true|echo <int>)` within 4 lines of a numeric `-eq/-ne/
  -lt/-le/-gt/-ge` test against the captured variable, when the variable
  is not normalised via `${var:-0}` or `${var//[^0-9]/}`, fails validate.
  Catches backticks, `awk`, `python3`, `jq`, and any future substitution
  tool with one rule instead of whack-a-mole. New umbrella allowlist
  `# task-spec:allow-numeric-fallback` covers the legitimate exceptions.
- **WS-C — Honest renaming.** The "HMAC envelope" terminology was
  swept across `SKILL.md`, `README.md`, `references/concepts/signed-off.md`,
  `references/concepts/agent-contract.md`, `agents/task-architect.md`,
  `runbooks/dispatching-a-task-spec.md`, `runbooks/first-spec-walkthrough.md`,
  `tests/test-portability-e2e.sh`, `tests/test-task-spec-skill.sh`,
  `scripts/validate-task-spec.sh`, `scripts/generate-task-spec.sh`, and
  `tests/conformance/T-conformance-003-no-signed-off-mod.md` and replaced
  with "structural sign-off envelope." A new honest paragraph in
  `references/concepts/signed-off.md` describes the limitation and the
  v2.2 crypto options. A new `tests/fixtures/T-20260603-fake-envelope.md`
  fixture proves the bypass and is itself the documentation: yes, this is
  possible; here is how; we say so out loud. CHANGELOG keeps the historical
  v2.1.0 entry intact (no retroactive edits) and adds this retraction
  paragraph above it.
- **WS-D — Backlog-dir consistency + dogfood lint (Bugs 6, 7).**
  `transition-status.sh` now writes the metrics ledger to
  `$TASKSPEC_BACKLOG_DIR/_metrics.jsonl` instead of the hardcoded
  `tasks/_metrics.jsonl` — the skill now follows its own published rules
  about backlog-dir configurability. A new `ts_metrics_path()` helper in
  `_lib.sh` is the single source of truth so future ledger writers cannot
  re-introduce the drift. The dead `warn_count=$(echo ... | grep -c '^\s\+-'
  || true)` assignment in `safe-to-delegate.sh` (the gate using the very
  anti-pattern it bans) is deleted. `lint-skill-docs.sh` adds **Check 10**:
  run the Check 16 regex set against every `scripts/*.sh` (excluding
  `validate-task-spec.sh` itself, which contains the regexes as string
  literals) and assert zero matches. The skill now eats its own dog food.
- **WS-E — Machine-readable schemas + reference consumers (G1, G6).**
  `references/schemas/task-spec-frontmatter.schema.json` and
  `references/schemas/agent-contract.schema.json` (JSON Schema draft
  2020-12) mirror the validator's Check 2 / 2b / 2c and the validation-card
  YAML block. `references/schemas/README.md` ships copy-pasteable
  validation snippets for Python (`jsonschema`), Node (`ajv`), Go
  (`gojsonschema`), and Rust (`jsonschema`). `references/examples/
  consume-task-spec.py` (~100 LOC, stdlib-only) and `consume-task-spec.ts`
  (~120 LOC, `yaml`+`ajv`) prove that any agent — Python, Node, anything
  with a JSON Schema validator — can parse a Task-Spec, extract its
  agent contract, enumerate eval blocks, and return a structured object
  **without invoking bash**. New `validate-task-spec.sh --emit-schema
  {frontmatter|agent-contract}` flag is the single source of truth so
  engine vendors can pin a specific schema version. `tests/
  test-portability-e2e.sh` extends with a schema-fidelity step that runs
  the Python consumer against the golden fixture and asserts exit 0
  with correct field extraction.
- **WS-F — Per-engine dispatch recipes (G2).** New
  `runbooks/dispatch-recipes/` directory ships one recipe per
  `execution_backend` enum value: `claude-code.md` (`Task()` tool
  invocation, `agent_contract.read` zone consumption, terminal-output
  reporting), `codex.md` (Codex CLI + `codex_metadata` + exit-code
  conventions), `kimi.md` (Kimi-specific content extracted from the old
  Kimi-centric runbook), `gemini.md` (generic LLM CLI / completion API
  path), `taskship.md` (taskship-specific command), `anthive.md`
  (parallel-session dispatch + `output_artifacts` capture), and
  `custom.md` (the DIY escape hatch + v2.2 `dispatch_recipe:` field
  reference). Each recipe is bounded to ~80 LOC and structured
  identically (Prerequisites / Dispatch / Status reporting / Failure
  modes / See also). `runbooks/dispatching-a-task-spec.md` is rewritten
  as a **router** with a "Pick your engine" jump table at the top — the
  Kimi-centricity critique is closed.
- **WS-G — RFC-2119 contract + conformance suite (G4).**
  `references/concepts/agent-contract.md` "The contract" section is
  rewritten with explicit RFC-2119 verbs (MUST, MUST NOT, SHOULD,
  SHOULD NOT, MAY). 38 keywords now appear in the contract document
  (target was ≥10). A new "Conformance Test Suite" section enumerates
  the synthetic scenarios any engine claiming Task-Spec support must
  pass, and `tests/conformance/` ships **6 conformance fixtures**
  (`T-conformance-001-status-lock.md` through
  `T-conformance-006-do-not-touch.md`) designed to be vendored by
  engine authors into their own test suites. New `tests/conformance/
  README.md` documents the vendoring protocol. A new "What this
  contract does NOT cover" section in `agent-contract.md` lists the
  deliberate non-requirements (e.g., engines MAY use any internal LLM
  model; the contract is execution-side, not generation-side).

### Changed

- **Version bumped to 2.1.1** in `scripts/_lib.sh` (`TASKSPEC_VERSION`)
  and `SKILL.md` frontmatter (`version:`). `plugin.json` and
  `marketplace.json` version fields bumped to match.
- **`lint-skill-docs.sh` now runs 10 checks** (was 9). The new Check 10
  is the WS-D dogfood lint — same regex set as `validate-task-spec.sh`
  Check 16, applied to the skill's own `scripts/*.sh`.
- **`runbooks/dispatching-a-task-spec.md` rewritten as a router**, with
  per-engine details delegated to `runbooks/dispatch-recipes/*.md`.
- **`references/index.md` (and `runbooks/first-spec-walkthrough.md`
  Step 7) updated** to point at the new recipe files and schema docs.

### Fixed

- **Bug 1.** Missing `signed_off_by:` under `signed_off:true` no longer
  produces a 0-byte silent abort.
- **Bug 2.** `safe-to-delegate.sh --stamp` no longer silently no-ops on
  specs missing the envelope lines.
- **Bug 3.** Backtick form of the inverted-grep-c pattern is now caught
  by the generic Check 16 rule.
- **Bug 4.** `awk`, `python3`, `jq`, and any other substitution tool
  with a numeric-fallback footgun is now caught by the same rule.
- **Bug 5.** Default `tests/test-task-spec-skill.sh` invocation (no
  `--suite` flag) runs to completion past Step 1.
- **Bug 6.** `transition-status.sh` honors `TASKSPEC_BACKLOG_DIR` for
  the metrics ledger.
- **Bug 7.** Dead `warn_count` assignment using the banned inverted
  pattern removed from `safe-to-delegate.sh`.
- **Bug 8 (honesty).** "HMAC envelope" terminology is retracted and
  replaced with "structural sign-off envelope" everywhere except the
  v2.1.0 CHANGELOG entry (which is preserved as historical record).

### Deferred to v2.2

- **Real HMAC crypto on the sign-off envelope** (with key management +
  rotation). Requires a real secrets-management surface — `.git/info/
  task-spec-key`, gitignore policy, "what if key missing" UX. The
  v2.1.1 rename + the `T-20260603-fake-envelope.md` fixture proving
  the limitation are honest enough for this release; the crypto upgrade
  is the v2.2 unlock.
- **`dispatch_recipe:` custom-engine frontmatter field.** Requires a
  frontmatter schema bump. Holding until at least one real "custom"
  engine asks for it. `runbooks/dispatch-recipes/custom.md` documents
  the v2.2 path so vendors know what to expect.
- **Bash 3.2 vs 5.x + macOS / Linux / WSL matrix CI.** Requires
  GitHub Actions infra wiring. Local `test-portability-e2e.sh` is
  sufficient for v2.1.1; matrix CI is the next-level proof.
- **`scripts/conformance-check.sh <engine-binary>` driver.** Presupposes
  WS-G's conformance fixtures exist (this release ships them as files).
  Build the driver in v2.2 once vendors actually want it.
- **Property-based eval fuzzer.** The WS-B generic rule + 4 new
  inverted-eval fixtures cover the observed variants. Property fuzzer
  adds combinatorial coverage; deferred to v2.2 per the v2.1.0 CHANGELOG.
- **MCP self-provisioning preflight.** Failure mode is loud
  (`mcp: server not found`); manual install remains acceptable.

---

## [2.1.0] — 2026-06-02

The "no rough edges" hardening release. Closes the four defects exposed by the
ADF Decimal pilot crank and Codex adversarial review.

### Added
- **Single canonical version field.** `version: "2.1.0"` in `SKILL.md` frontmatter
  and `TASKSPEC_VERSION="2.1.0"` in `scripts/_lib.sh`. Every top-level script
  sources `_lib.sh` and supports `--version` printing `task-spec v2.1.0`.
- **CHANGELOG.md** (this file). Required to bump for every release per the format
  change protocol documented in `_lib.sh`.
- **`scripts/_lib.sh`** — shared bash helpers (path resolution, error printing,
  version handler). Single source of truth for version + skill root + configurable
  `TASKSPEC_BACKLOG_DIR`.
- **Inverted-grep-c lint** (WS4) — `validate-task-spec.sh` rejects 6 known
  inverted-eval-count variants (e.g. `count=$(grep -c X file || echo 0)` produces
  the literal string `"0\n0"` on zero matches, breaking integer comparison).
- **Eval-inversion fixture suite** (WS5) — `tests/fixtures/` ships 7 minimal
  fixture specs + `oracle.json` declaring expected verdicts, consumed by
  `tests/test-task-spec-skill.sh --suite fixtures`.
- **`safe-to-delegate.sh --stamp` is now THE named gate** (WS3) — the
  documented author flow points at the gate, not at the structural-only
  `validate-task-spec.sh`. New `references/concepts/signed-off.md` explains the
  autonomy contract; new `runbooks/dispatching-a-task-spec.md` closes the loop.
- **Portable distribution** (WS6) — `plugin.json` + `marketplace.json` ship at
  the skill root; `scripts/install.sh` rewrites for fresh-tempdir installability;
  `TASKSPEC_BACKLOG_DIR` env var overrides hardcoded `tasks/` for downstream users.
- **First-spec walkthrough + portability e2e smoke test** (WS8) — a new author
  at a new repo can follow `runbooks/first-spec-walkthrough.md` and produce a
  `signed_off: true` spec on first attempt; `tests/test-portability-e2e.sh`
  enforces it in CI.
- **Doc-consistency lint** (WS10) — `scripts/lint-skill-docs.sh` blocks future
  v1/v2 drift, version mismatches, and missing distribution files.

### Changed
- **All docs canonicalised to v2.1.** Every `Task-Spec v1` reference outside this
  CHANGELOG was swept to `Task-Spec v2.1`. Future-tense `v2 will add` roadmap
  lines were replaced with concrete CHANGELOG entries.
- **`generate-task-spec.sh` self-validates** (WS7) — on success, runs
  `validate-task-spec.sh` against its own output and prints a `Next: ...
  safe-to-delegate.sh --stamp ...` breadcrumb so authors are never lost between
  generation and gating.
- **`task-architect` agent template aligned** (WS9) — references v2.1,
  `execution_backend`, `signed_off`, and contains the "never hand-stamp" rule.

### Fixed
- **`validate-task-spec.sh:362` self-trip.** The script itself used
  `PLACEHOLDER_COUNT=$(grep -c '{{TODO' "$FILE" 2>/dev/null || echo 0)` — exactly
  the inverted-grep-c pattern the new lint catches. Rewritten using
  `${count:-0}` normalisation so the lint catches zero legitimate code in the
  skill itself.

### Deferred to v2.2
- MCP self-provisioning preflight (failure mode is loud; manual install
  acceptable for v2.1).
- Property-based eval fuzzer (curated fixture oracle suffices for v2.1).
- Per-file authorized-fields intent gate (belongs in the broker, not the spec
  skill).
- Backfill of v1/v0 CHANGELOG history (see git history).

---

## [2.0.0] — 2026-05-19

Initial v2 format release. See git history for the full change set; key additions
included the `signed_off` autonomy contract, `execution_backend` routing field,
`creates_paths` for greenfield tasks, `check_type: deterministic | llm_judge`
on per-eval validation, the 6-zone format (Intent / Contract / Rollback /
Observability / Guardrails / Operations), and `safe-to-delegate.sh --stamp` as
the autonomy-contract producer.

---

## [1.0.0] — 2026-05-19

Initial public release. The 4-zone EDD format with frontmatter + runnable bash
evals + validation card. See git history for the full change set.
