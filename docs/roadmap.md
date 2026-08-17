# Roadmap — after the 3.9 execution control plane

Engine 3.9 adds the optional TaskMesh control plane on top of the 3.8
revision-bound trust chain: HMAC v3 authorization, attempt-bound
handoffs/receipts, commit-aware scope checks, durable acceptance records, a
derived graph, and read-only lifecycle status. Format v3 remains the authoring
default.

Priorities are ordered. P0 proves the claims, P1 deepens verification, P2 builds
the ecosystem, P3 is tooling.

## P0 — prove the claims

- **P0-1 Multi-engine CI proof.** Execute and retain real-engine evidence for the
  nine-family `EngineMatrix/v1`; at least Codex and Claude must run in guarded CI
  before a real-engine badge is published. The v3.7 harness is shipped, but all
  release-template entries remain honestly disabled.
- **P0-2 Doc-drift sweep.** Hunt remaining stale version claims across `docs/`
  and `harness/` (`spec/` and the schemas were fixed at extraction).
- **P0-3 Standalone-checkout verification.** Verify `taskspec doctor` plus the
  full test suite run clean on a fresh machine with no converge repo present —
  this repo must stand alone.

## P1 — deepen verification

- **P1-1 Sealed holdout evals (format v4). — SHIPPED 3.7.0.** Private bundles,
  public descriptors, and policy-bound receipts.
- **P1-2 Graded and human evidence. — SHIPPED 3.7.0.** Typed external receipts
  with rubric/threshold/owner binding; evaluator implementation remains external.
- **P1-3 Mutation matrix. — FOUNDATION SHIPPED 3.7.0.** Baseline plus
  patch-matrix audit. Graduating repository-specific Python, JavaScript, Go, and
  Bash mutation patches from the checked-in experimental manifest shapes remains.
- **P1-4 Key management. — FOUNDATION SHIPPED 3.7.0.** Ed25519 identity and
  revocation exist; remote trust distribution and policy remain.
- **P1-5 Security pass.** Sanitize untrusted spec/tracker text at
  context-assembly time; sandbox doctrine for unattended execution; make T1
  (signed+sealed) the only tier eligible for unsupervised dispatch. Integrating a
  production sandbox that can truthfully issue environment receipts is part of
  this.

## P2 — build the ecosystem

- **P2-1 MCP server. — READ-ONLY FOUNDATION SHIPPED 3.7.0.** Validate and handoff
  tools are exposed; state-changing claim/submit/report tools remain
  intentionally out of scope.
- **P2-2 A2A alignment. — ENVELOPE FOUNDATION SHIPPED 3.7.0.** Task ID and digest
  survive the bridge. Validating the bridges against third-party A2A/MCP
  implementations remains — the current envelopes preserve Task-Spec identity but
  are not a certification claim.
- **P2-3 Tracker adapters via MCP.** github/linear/jira behind one thin MCP
  client (create/transition/link), replacing bespoke adapter code.
- **P2-4 Environment contract. — CONTRACT SHIPPED 3.7.0.** Digest and receipt
  binding exist; a production sandbox/orchestrator must perform actual
  enforcement.
- **P2-5 Distribution.** Versioned releases with a schema freeze per release;
  homebrew/curl installer.
- **P2-6 Conformance badge program.** Third-party executors certify L2 and get
  listed, backed by retained external evidence.

## P3 — tooling

- **P3-1 Eval packs per stack** (dbt control-sum patterns, terraform plan checks,
  pytest/API contract evals) — shareable verification libraries.
- **P3-2 Rewire converge's Pass 5B skill** to consume this engine (thin skill
  delegating to the CLI) and delete the duplicated scripts there — cross-repo
  change.
- **P3-3 Fleet metrics.** Acceptance rate, retry distribution, cost-per-green
  dashboards fed by `_metrics.jsonl`.

Any future format change still requires schema, conformance, template,
validator, examples, and changelog updates together — see `AGENTS.md`.
