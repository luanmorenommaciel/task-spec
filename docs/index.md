# Task-Spec Knowledge Base

> **Purpose**: KB for the `task-spec` engine — the format, methodology, and patterns.
> **Owner repo**: the task-spec engine repo (this file lives at `docs/index.md`)
> **Owner Agent**: `agents/task-architect.md`
> **MCP Validated**: 2026-05-19

---

## Concepts (≤150 lines each)

| File | Purpose |
|------|---------|
| [../spec/task-spec-v3.md](../spec/task-spec-v3.md) | Stable format-v3 compatibility contract |
| [../spec/task-spec-v4.md](../spec/task-spec-v4.md) | Opt-in evidence, identity, environment, and portability policy |
| [concepts/eval-driven-development.md](concepts/eval-driven-development.md) | EDD methodology |
| [concepts/edd-vs-sdd-honest-comparison.md](concepts/edd-vs-sdd-honest-comparison.md) | When to use which |
| [concepts/six-zones.md](concepts/six-zones.md) | File anatomy |
| [concepts/profiles.md](concepts/profiles.md) | **v3** effort-scaled profiles (lite/standard/full) + the behavior↔eval traceability rule |
| [concepts/conformance-levels.md](concepts/conformance-levels.md) | **v3** executor conformance L0/L1/L2 + the A2A lifecycle mapping |
| [concepts/decomposition.md](concepts/decomposition.md) | **v3** intent/PRD → N atoms: the flat index+detail shape, holes-as-blockers, profile-per-atom, `depends_on`/`parent` edges |
| [concepts/effort-gate.md](concepts/effort-gate.md) | XS/S/M/L leaves and XL/XXL composition rules |
| [concepts/agent-contract.md](concepts/agent-contract.md) | Cross-vendor contract |
| [concepts/signed-off.md](concepts/signed-off.md) | **The autonomy contract** — who produces `signed_off: true`, what it asserts, why hand-stamping is forbidden |
| [concepts/backlog-architecture.md](concepts/backlog-architecture.md) | 5-layer state management |
| [concepts/evaluation-policy.md](concepts/evaluation-policy.md) | Deterministic, holdout, graded, and human acceptance policy |
| [concepts/evidence-receipts.md](concepts/evidence-receipts.md) | Typed evidence and provenance contracts |
| [concepts/environment-contract.md](concepts/environment-contract.md) | Portable runtime commitment and enforcement receipt |

## Patterns (≤200 lines each)

| File | Purpose |
|------|---------|
| [patterns/runnable-bash-evals.md](patterns/runnable-bash-evals.md) | Writing terminal, idempotent evals |
| [patterns/validation-card-yaml.md](patterns/validation-card-yaml.md) | The YAML contract mirror |
| [patterns/atomic-status-transitions.md](patterns/atomic-status-transitions.md) | The 7-step transition protocol |
| [patterns/anti-patterns-extraction.md](patterns/anti-patterns-extraction.md) | Mining Zone 3 from MCP research |
| [patterns/do-not-touch-detection.md](patterns/do-not-touch-detection.md) | Repo-scan patterns |

## Quick Reference

| File | Purpose |
|------|---------|
| [quick-reference.md](quick-reference.md) | One-page cheatsheet |

## Runbooks (in `../runbooks/`)

| File | Purpose |
|------|---------|
| [../runbooks/first-spec-walkthrough.md](runbooks/first-spec-walkthrough.md) | **Your first 10 minutes** — install → generate → validate → gate end-to-end |
| [../runbooks/from-fuzzy-intent.md](runbooks/from-fuzzy-intent.md) | Paragraph → Task-Spec |
| [../runbooks/decomposing-intent.md](runbooks/decomposing-intent.md) | **Intent / PRD / set-of-calls → N linked atomic specs** — flat index + detail atoms, `depends_on` edges, holes-as-blockers |
| [../runbooks/from-meeting-note.md](runbooks/from-meeting-note.md) | Krisp output → Task-Spec |
| [../runbooks/from-existing-task.md](runbooks/from-existing-task.md) | Legacy → v2.1 conversion |
| [../runbooks/validating-a-task-spec.md](runbooks/validating-a-task-spec.md) | Pre-gate structural linter walkthrough |
| [../runbooks/dispatching-a-task-spec.md](runbooks/dispatching-a-task-spec.md) | **What to do after `safe-to-delegate.sh --stamp`** — router to per-engine recipes |
| [../runbooks/recovering-from-crash.md](runbooks/recovering-from-crash.md) | State recovery |
| [../runbooks/empirical-experiment-protocol.md](runbooks/empirical-experiment-protocol.md) | SDD vs EDD experiment |

## Dispatch Recipes (in `../adapters/engines/`)

Per-engine recipes routed from `dispatching-a-task-spec.md`. Each follows the same five-section shape: Prerequisites / Dispatch command / Status reporting / Failure modes / See also.

| File | Engine |
|------|--------|
| [../adapters/engines/claude-code.md](../adapters/engines/claude-code.md) | Claude Code (Task() tool, subagent delegation) |
| [../adapters/engines/codex.md](../adapters/engines/codex.md) | Codex CLI (`codex run --task ...`) |
| [../adapters/engines/kimi.md](../adapters/engines/kimi.md) | Kimi CLI via the 12-stage broker pipeline |
| [../adapters/engines/gemini.md](../adapters/engines/gemini.md) | Gemini / generic completion-API CLIs |
| [../adapters/engines/taskship.md](../adapters/engines/taskship.md) | taskship runtime |
| [../adapters/engines/anthive.md](../adapters/engines/anthive.md) | anthive parallel-session dispatch |
| [../adapters/engines/custom.md](../adapters/engines/custom.md) | DIY escape hatch (v2.2 `dispatch_recipe:` field) |

---

## How the agent navigates this KB

The `task-architect` agent reads from this folder:

1. **Start with** `../spec/task-spec-v3.md` for stable tasks or `../spec/task-spec-v4.md` when evidence policy is required
2. **Concepts** for definitional questions ("what IS an effort gate?")
3. **Patterns** for implementation questions ("how do I write an idempotent eval?")
4. **Runbooks** for workflow questions ("how do I convert a meeting note?")

Cross-link with `[[concept-name]]` syntax. Validate against Context7 MCP at runtime.
