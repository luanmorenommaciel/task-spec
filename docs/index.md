# Task-Spec documentation

The knowledge base for the `task-spec` engine — the format, the methodology, the
patterns, and the runtime contracts. The normative contract is `../spec/` plus
the conformance suite; everything here explains it.

Owner agent: [`../harness/agents/task-architect.md`](../harness/agents/task-architect.md).

## Start here

| File | Purpose |
|------|---------|
| [getting-started/index.md](getting-started/index.md) | Orientation and the shortest path in |
| [getting-started/installation.md](getting-started/installation.md) | Install the engine and the skill across harnesses |
| [getting-started/first-task.md](getting-started/first-task.md) | Your first authored, gated, accepted task |
| [getting-started/reviewer-route.md](getting-started/reviewer-route.md) | Review the repo in five minutes |
| [getting-started/taskmesh.md](getting-started/taskmesh.md) | The optional multi-harness execution control plane |
| [quick-reference.md](quick-reference.md) | One-page command cheatsheet |
| [authoring-workflow.md](authoring-workflow.md) | The authoring doctrine shipped with the installed skill |
| [roadmap.md](roadmap.md) | Prioritized remaining work (P0–P3) |

## The format

| File | Purpose |
|------|---------|
| [../spec/README.md](../spec/README.md) | Orientation for the normative contract and the triple-lock rule |
| [../spec/task-spec-v3.md](../spec/task-spec-v3.md) | Stable format-v3 compatibility contract |
| [../spec/task-spec-v4.md](../spec/task-spec-v4.md) | Opt-in evidence, identity, environment, and portability policy |
| [concepts/six-zones.md](concepts/six-zones.md) | File anatomy |
| [concepts/profiles.md](concepts/profiles.md) | Effort-scaled profiles plus the behavior↔eval traceability rule |
| [concepts/effort-gate.md](concepts/effort-gate.md) | XS/S/M/L leaves and XL/XXL composition rules |
| [concepts/decomposition.md](concepts/decomposition.md) | Intent or PRD → N atoms: flat index+detail, holes-as-blockers, `depends_on`/`parent` edges |
| [concepts/agent-contract.md](concepts/agent-contract.md) | Cross-vendor executor contract |
| [concepts/backlog-architecture.md](concepts/backlog-architecture.md) | Five-layer state management |

## Methodology

| File | Purpose |
|------|---------|
| [concepts/eval-driven-development.md](concepts/eval-driven-development.md) | EDD methodology |
| [concepts/edd-vs-sdd-honest-comparison.md](concepts/edd-vs-sdd-honest-comparison.md) | When to use which |
| [concepts/evaluation-policy.md](concepts/evaluation-policy.md) | Deterministic, holdout, graded, and human acceptance policy |
| [concepts/conformance-levels.md](concepts/conformance-levels.md) | Executor conformance L0/L1/L2 and the A2A lifecycle mapping |

## Trust and evidence

| File | Purpose |
|------|---------|
| [concepts/signed-off.md](concepts/signed-off.md) | The autonomy contract — who writes `signed_off: true` and why hand-stamping is forbidden |
| [concepts/evidence-receipts.md](concepts/evidence-receipts.md) | Typed evidence and provenance contracts |
| [concepts/environment-contract.md](concepts/environment-contract.md) | Portable runtime commitment and enforcement receipt |
| [trust/index.md](trust/index.md) | Trust surface overview |
| [trust/threat-model.md](trust/threat-model.md) | What the gates do and do not defend against |
| [trust/taskmesh-boundaries.md](trust/taskmesh-boundaries.md) | Supervised/autonomous assurance and credential boundaries |

## Patterns

| File | Purpose |
|------|---------|
| [patterns/runnable-bash-evals.md](patterns/runnable-bash-evals.md) | Writing terminal, idempotent evals |
| [patterns/validation-card-yaml.md](patterns/validation-card-yaml.md) | The YAML contract mirror |
| [patterns/atomic-status-transitions.md](patterns/atomic-status-transitions.md) | The transition protocol |
| [patterns/anti-patterns-extraction.md](patterns/anti-patterns-extraction.md) | Mining Zone 3 from research |
| [patterns/do-not-touch-detection.md](patterns/do-not-touch-detection.md) | Repository-scan patterns |

## Guides

| File | Purpose |
|------|---------|
| [guides/index.md](guides/index.md) | Guide index |
| [guides/multi-harness.md](guides/multi-harness.md) | One contract across several executors |
| [guides/multi-engine-evidence.md](guides/multi-engine-evidence.md) | Running and retaining the engine matrix |
| [guides/replanning-and-recovery.md](guides/replanning-and-recovery.md) | When the contract has to change |
| [guides/repository-scan.md](guides/repository-scan.md) | Grounding a spec in real repository evidence |
| [guides/research-providers.md](guides/research-providers.md) | Optional cited-research adapters |

## Runbooks

| File | Purpose |
|------|---------|
| [runbooks/first-spec-walkthrough.md](runbooks/first-spec-walkthrough.md) | Your first ten minutes, end to end |
| [runbooks/from-fuzzy-intent.md](runbooks/from-fuzzy-intent.md) | Paragraph → Task-Spec |
| [runbooks/decomposing-intent.md](runbooks/decomposing-intent.md) | Intent or PRD → N linked atomic specs |
| [runbooks/batch-sprint-compose.md](runbooks/batch-sprint-compose.md) | Composing a sprint from an approved plan |
| [runbooks/from-meeting-note.md](runbooks/from-meeting-note.md) | Meeting output → Task-Spec |
| [runbooks/from-existing-task.md](runbooks/from-existing-task.md) | Legacy checklist conversion |
| [runbooks/validating-a-task-spec.md](runbooks/validating-a-task-spec.md) | Pre-gate structural linter walkthrough |
| [runbooks/dispatching-a-task-spec.md](runbooks/dispatching-a-task-spec.md) | What to do after the PRE-gate seals a spec |
| [runbooks/recovering-from-crash.md](runbooks/recovering-from-crash.md) | State recovery |
| [runbooks/empirical-experiment-protocol.md](runbooks/empirical-experiment-protocol.md) | SDD vs EDD experiment protocol |
| [runbooks/dark-factory-as-task-spec.md](runbooks/dark-factory-as-task-spec.md) | Unattended execution, honestly scoped |
| [runbooks/skill-hardening-blueprint.md](runbooks/skill-hardening-blueprint.md) | Hardening a skill against drift |

## Reference

| File | Purpose |
|------|---------|
| [reference/index.md](reference/index.md) | Reference index |
| [reference/cli.md](reference/cli.md) | Generated CLI table — regenerate with `python3 tools/render-cli-reference.py --write docs/reference/cli.md` |
| [reference/contracts.md](reference/contracts.md) | Contract catalog |
| [reference/acceptance-contracts.md](reference/acceptance-contracts.md) | Acceptance record and failure codes |
| [reference/task-revision.md](reference/task-revision.md) | `TaskRevision/v1` authority manifest |
| [reference/task-graph-view.md](reference/task-graph-view.md) | `TaskGraphView/v1` derived graph |
| [reference/taskmesh-contracts.md](reference/taskmesh-contracts.md) | TaskMesh API, runtime overlay, leases, states, and errors |
| [reference/compatibility-policy.md](reference/compatibility-policy.md) | What may change in a minor release |
| [reference/converge-donor-map.md](reference/converge-donor-map.md) | Provenance of the extraction from converge |

## Dispatch recipes

Per-engine recipes routed from [runbooks/dispatching-a-task-spec.md](runbooks/dispatching-a-task-spec.md).
Each follows the same shape: prerequisites, dispatch command, status reporting,
failure modes, see also.

| File | Engine |
|------|--------|
| [../harness/engines/claude-code.md](../harness/engines/claude-code.md) | Claude Code |
| [../harness/engines/codex.md](../harness/engines/codex.md) | Codex CLI |
| [../harness/engines/kimi.md](../harness/engines/kimi.md) | Kimi CLI |
| [../harness/engines/gemini.md](../harness/engines/gemini.md) | Gemini and generic completion-API CLIs |
| [../harness/engines/taskship.md](../harness/engines/taskship.md) | taskship runtime |
| [../harness/engines/anthive.md](../harness/engines/anthive.md) | anthive parallel-session dispatch |
| [../harness/engines/custom.md](../harness/engines/custom.md) | DIY escape hatch |

## How to navigate

1. Start with `../spec/task-spec-v3.md` for stable work, or `../spec/task-spec-v4.md`
   when independent evidence policy is required.
2. Read **concepts** for definitional questions ("what is an effort gate?").
3. Read **patterns** for implementation questions ("how do I write an idempotent eval?").
4. Read **guides** for how-to questions. Existing **runbooks** stay as historical
   walkthroughs; that directory is closed — new how-tos belong in `guides/`.
5. Read **reference** for exact contract fields and CLI behavior.
