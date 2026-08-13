# Trust and operational boundaries

Task-Spec assumes the executor may be hostile and may write or commit inside the
repository. Author and evaluator private keys must remain outside the executor
environment. Markdown Task-Specs and Git history are authoritative; indexes,
graphs, records catalogs, and metrics are rebuildable projections.

| Mechanism | Proves | Does not prove |
|---|---|---|
| HMAC v3 | A repository-key holder sealed one exact `TaskRevision/v1` | Human identity, non-repudiation, key secrecy, or isolation |
| PRE-gate | Structure, eval-shell quality, graph readiness, and authorization tier | That future work is correct |
| TaskHandoff/v3 | One revision was issued as one attempt from one Git base and dependency closure | That an executor ran or obeyed it |
| POST-gate | Evals, Git/worktree blast radius, revision, closure, and configured evidence passed | Deployment, production health, or perfect semantics |
| v2 receipt | One named surface reported an observation for one exact subject | That the evaluator is wise, complete, or honest |
| Ed25519 evaluator signature | Receipt bytes came from a key trusted for that receipt class | Organizational authority or semantic truth |
| Environment receipt | A named external provider reported enforcement for this attempt | A sandbox merely because JSON exists |
| AcceptanceRecord/v1 | The accepted attempt, gates, tier, and receipt digests were durably recorded | Production success beyond the configured contract |
| Conformance L0–L2 | An adapter honors the tested format and lifecycle behavior | Fleet reliability, hosted service quality, or certification |

Existence-only evals are blocked for blind delegation unless explicitly
supervised or annotated. HMAC v1/v2 and receipt v1 remain compatibility inputs,
but are Tier 2. Skipping the blast-radius gate or accepting without a verifiable
key also forces Tier 2 and requires explicit supervisor identity and reason.

Research evidence may inform context, constraints, and risks. It cannot
authorize work or satisfy acceptance. DSSE proves signed bytes, not truth.
A2A and MCP are optional transports, not normative trust dependencies.

Read the full [threat model](threat-model.md),
[authorization contract](../concepts/signed-off.md), and
[acceptance contracts](../reference/acceptance-contracts.md) before granting
unsupervised Tier 1.
