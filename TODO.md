# TODO — the task-spec engine roadmap

Prioritized. P0 proves the claims, P1 deepens verification, P2 builds the ecosystem, P3 tooling.

## P0 — prove the claims

- **P0-1 Multi-engine CI proof.** Execute and retain real-engine evidence for the nine-family `EngineMatrix/v1`; at least Codex and Claude must run in guarded CI before a real-engine badge is published. The v3.7 harness is shipped, but all release-template entries remain honestly disabled.
- **P0-2 Doc-drift sweep.** Hunt remaining 4-vs-6-zone prose, stale version claims, and any leftover references to the origin repo's old name/paths across `docs/` and `adapters/` (`spec/` and the schemas were fixed at extraction).
- **P0-3 Standalone-checkout verification.** Verify `taskspec doctor` + the full test suite run clean on a fresh machine with no converge repo present — this repo must stand alone.

## P1 — deepen verification

- **P1-1 Sealed holdout evals (format v4). — SHIPPED 3.7.0.** Private bundles, public descriptors, and policy-bound receipts.
- **P1-2 Graded and human evidence. — SHIPPED 3.7.0.** Typed external receipts with rubric/threshold/owner binding; evaluator implementation remains external.
- **P1-3 Mutation matrix. — FOUNDATION SHIPPED 3.7.0.** Baseline plus patch-matrix audit; stack-specific mutation packs remain.
- **P1-4 Key management. — FOUNDATION SHIPPED 3.7.0.** Ed25519 identity and revocation exist; remote trust distribution remains.
- **P1-5 Security pass (from converge B-13).** Sanitize untrusted spec/tracker text at context-assembly time; sandbox doctrine for unattended execution; make T1 (signed+sealed) the only tier eligible for unsupervised dispatch.

## P2 — build the ecosystem

- **P2-1 MCP server. — READ-ONLY FOUNDATION SHIPPED 3.7.0.** Validate and handoff tools are exposed; state-changing claim/submit/report tools remain intentionally out of scope.
- **P2-2 A2A alignment. — ENVELOPE FOUNDATION SHIPPED 3.7.0.** Task ID and digest survive the bridge; third-party protocol certification remains.
- **P2-3 Tracker adapters via MCP.** github/linear/jira behind one thin MCP client (create/transition/link), replacing bespoke adapter code.
- **P2-4 Environment contract. — CONTRACT SHIPPED 3.7.0.** Digest and receipt binding exist; a production sandbox/orchestrator must perform actual enforcement.
- **P2-5 Distribution.** Versioned releases with a schema freeze per release; homebrew/curl installer.
- **P2-6 Conformance badge program.** Third-party executors certify L2 and get listed.

## P3 — tooling

- **P3-1 Eval packs per stack** (dbt control-sum patterns, terraform plan checks, pytest/API contract evals) — shareable verification libraries.
- **P3-2 Rewire converge's Pass 5B skill** to consume this engine (thin skill delegating to the CLI) and delete the duplicated scripts there — cross-repo change.
- **P3-3 Fleet metrics.** Acceptance rate, retry distribution, cost-per-green dashboards fed by `_metrics.jsonl`.
