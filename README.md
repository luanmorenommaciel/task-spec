# task-spec

**The open, atomic, self-verifying unit of work for autonomous agentic systems.**

<!-- badges: conformance / CI evidence lands with P0-1 (see TODO.md) -->
[![format](https://img.shields.io/badge/format-v3-blue)](spec/task-spec-v3.md)
[![version](https://img.shields.io/badge/version-3.3.0-green)](VERSION)
[![license](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

## The 60-second pitch

A task-spec is a single markdown file: YAML frontmatter + six zones + **runnable
bash evals**. An eval that runs green *is* the definition of done — not a
checklist an agent claims to have finished. Two gates close the loop without
trusting the executor: a PRE-gate seals the eval bodies in an HMAC envelope and
flips `signed_off: true` (delegate-safe), a POST-gate re-runs the evals from a
clean checkout, checks the blast radius, and re-verifies the seal before
stamping `accepted: true` (work-is-real). Any executor that passes the L0/L1/L2
conformance suite can pick a spec up — Claude, Codex, Kimi, GLM, Gemini, or a
60-line bash loop. Vendor-neutral by construction, not by promise.

## Install

```bash
git clone https://github.com/luanmorenommaciel/task-spec.git
cd task-spec
ln -s "$PWD/bin/taskspec" /usr/local/bin/taskspec   # or anywhere on PATH
taskspec doctor                                      # sanity-check the toolchain

# optional: install the task-architect agent + thin skill into a repo
bash src/lib/install.sh --target /path/to/your/repo
```

## Quickstart

```bash
taskspec new verify-otel-pipeline S any notes/audit.md   # scaffold tasks/T-*.md
# ...fill the {{TODO}} stubs: title, why, goal, evals, anti-patterns...
taskspec validate tasks/T-*-verify-otel-pipeline.md      # structural linter
taskspec gate --stamp tasks/T-*-verify-otel-pipeline.md  # PRE-gate: seal + sign off
# hand the spec to any conformant executor, then:
taskspec accept --stamp tasks/T-*-verify-otel-pipeline.md  # POST-gate: prove it's real
```

## The format in 60 seconds

Six zones: **(1) Intent** (why / goal / context) · **(2) Contract** (Success
Criteria as runnable `eval_N()` bash, a YAML validation_card, an Exit Check that
calls every eval) · **(3) Rollback** · **(4) Observability** · **(5) Guardrails**
(anti-patterns, do-not-touch) · **(6) Operations** (open questions). A
`## Behavior` section (Given/When/Then with stable `B-N` ids) sits between
intent and evals, and the validator enforces **behavior↔eval traceability**:
every behavior is verified by ≥1 eval (`verifies: [B-N]`), every eval maps to a
declared behavior. The **effort gate** keeps atoms atomic: `XS/S/M` accepted,
`L` accepted only with `execution_backend: glm` and one coherent done-condition,
`XL` refused → route to SDD (AgentSpec / OpenSpec / SpecKit). Full spec:
[spec/task-spec-v3.md](spec/task-spec-v3.md).

## The dual gates

| | PRE-gate — `taskspec gate --stamp` | POST-gate — `taskspec accept --stamp` |
|---|---|---|
| Question | "Are these evals well-formed enough to delegate blind?" | "The executor claims done — is the work REAL?" |
| Runs evals | Yes — assertion failure is *expected* (work unbuilt); blocks only on broken bash | Yes — must PASS from a clean checkout |
| Blast radius | — | Changed files ⊆ `touches_paths`, ∩ `do-not-touch` = ∅ |
| Seal | Writes `signed_off*` + HMAC `signed_off_sig` over the eval bodies | Re-verifies the HMAC (evals not weakened post-gate) |
| Machine output | `TIER=1\|2` line (crypto trust / structural-only) | `ACCEPTED=1\|0`, stamps `accepted: true` |
| Opt-ins | `--require-tier1` (CI: no Tier-2 unsupervised) | `--gold-sanity` (evals must FAIL on the unpatched baseline) |

## For coding agents

`bin/taskspec` is a stable machine contract: fixed subcommand names, exit codes
(`0` success · `1` underlying check failed · `2` usage), `taskspec run --ci`
emitting one JSON object per eval on stdout, `taskspec doctor` for environment
self-checks. Integrations: [Claude Code skill](integrations/claude-code/),
[GitHub Action](integrations/github-action/) (the CI eval-gate — the merge gate
stops trusting agent-pasted GREEN), [Codex AGENTS.md](integrations/codex/AGENTS.md).

## Conformance

"Any conformant executor can pick it up" is testable, not aspirational:
**L0** reads the format and runs the evals · **L1** honors the status lifecycle
(ready → in-progress → done) · **L2** honors the retry budget (parks instead of
looping forever). The suite, fixtures, and vendoring protocol live in
[spec/conformance/](spec/conformance/); `taskspec conformance --self-test` runs
the bundled reference executor.

## Repo layout

```text
bin/taskspec        canonical CLI (stable subcommands + exit codes)
src/                engine scripts by verb: author/ gate/ accept/ backlog/ dispatch/ lib/
spec/               task-spec-v3.md + schemas/ + conformance/   ← the normative surface
docs/               authoring doctrine, concepts, patterns, runbooks, examples
agents/             task-architect agent · templates/ spec template
adapters/           engines/ (per-engine dispatch recipes) + trackers/ — NON-normative
integrations/       claude-code skill · github-action · codex
fixtures/diamond-6/ 6-task dependency-diamond backlog used by CI
configs/            signing-key setup · evals/ benchmark cases · tests/ self-test suite
```

## Honest boundary

Green evals ≠ correct outcomes. An eval proves what it asserts, nothing more;
`--gold-sanity` exists because always-true evals pass on the unpatched baseline
too. The HMAC envelope is tamper-**evident** (it proves eval bodies weren't
edited after the gate), not tamper-**proof** (a repo-key holder can reseal).
Humans stay at intent-setting and acceptance review — the loop in between runs
without them. Roadmap: [TODO.md](TODO.md) and [docs/roadmap.md](docs/roadmap.md).

## License

MIT — © 2026 Luan Moreno. See [LICENSE](LICENSE).
