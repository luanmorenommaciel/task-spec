# TODO — the task-spec engine roadmap

Prioritized. P0 proves the claims, P1 deepens verification, P2 builds the ecosystem, P3 tooling.

## P0 — prove the claims

- **P0-1 Multi-engine CI proof.** Run `fixtures/diamond-6` green via `ref-executor` AND ≥2 real engines (claude, codex) in GitHub Actions on every push; publish a results badge in the README. Turns "vendor-neutral" from a design property into evidence. *(Foundation landed in v3.4.0: credential-free CI runs `make check` on ubuntu+macOS and the README carries the badge. Remaining: the real-engine matrix on top of it.)*
- **P0-2 Doc-drift sweep.** Hunt remaining 4-vs-6-zone prose, stale version claims, and any leftover references to the origin repo's old name/paths across `docs/` and `adapters/` (`spec/` and the schemas were fixed at extraction).
- **P0-3 Standalone-checkout verification.** Verify `taskspec doctor` + the full test suite run clean on a fresh machine with no converge repo present — this repo must stand alone.

## P1 — deepen verification

- **P1-1 Sealed holdout evals (format v4).** A second eval block in the spec, HMAC-sealed, revealed only to accept at acceptance time — the StrongDM holdout trick inside the existing envelope. Workers cannot game evals they cannot read.
- **P1-2 Graded `check_type`.** Extend validation_card `check_type` beyond `deterministic` (`graded` = model-judged rubric, `human`) with a judge runner; closes the intent-faithfulness gap bash can't reach.
- **P1-3 Mutation matrix.** Generalize `--gold-sanity` into N realistic injected bugs; an eval that can't be forced RED is rejected at gate time.
- **P1-4 Key management.** Rotation, per-author signing identity, and a remote verification story for cross-repo fleet dispatch.
- **P1-5 Security pass (from converge B-13).** Sanitize untrusted spec/tracker text at context-assembly time; sandbox doctrine for unattended execution; make T1 (signed+sealed) the only tier eligible for unsupervised dispatch.

## P2 — build the ecosystem

- **P2-1 MCP server.** Expose the engine as MCP tools (next/claim/context/eval/submit/report) so any MCP-speaking agent consumes tasks natively — engines become protocol clients, not flags.
- **P2-2 A2A alignment.** task-spec as the verifiable payload inside A2A Task artifacts (extend the `ts_a2a_state` mapping; blocked→input-required etc.).
- **P2-3 Tracker adapters via MCP.** github/linear/jira behind one thin MCP client (create/transition/link), replacing bespoke adapter code.
- **P2-4 Environment contract.** Spec-declared setup/teardown hooks (make seed / devcontainer) the dispatcher guarantees before evals run — midnight runs forgive nothing.
- **P2-5 Distribution.** Versioned releases with a schema freeze per release; homebrew/curl installer.
- **P2-6 Conformance badge program.** Third-party executors certify L2 and get listed.

## P3 — tooling

- **P3-1 Eval packs per stack** (dbt control-sum patterns, terraform plan checks, pytest/API contract evals) — shareable verification libraries.
- **P3-2 Rewire converge's Pass 5B skill** to consume this engine (thin skill delegating to the CLI) and delete the duplicated scripts there — cross-repo change.
- **P3-3 Fleet metrics.** Acceptance rate, retry distribution, cost-per-green dashboards fed by `_metrics.jsonl`.
