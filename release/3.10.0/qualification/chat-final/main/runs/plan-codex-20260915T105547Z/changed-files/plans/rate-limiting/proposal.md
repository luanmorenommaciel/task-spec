# Rate-limiting steel thread — proposed plan

Status: proposed, with open review blockers. Nothing is approved or executed.

## Scope and ownership

Provider-owned usage metering stays provider-owned and out of scope. Request-window counters and decision telemetry serve rate limiting only. Production storage and deployment infrastructure remain unselected. The source is a synthetic fixture, not proof of shipped behavior.

The blueprint names no responsible owner for the in-scope work. Ownership is explicitly unassigned pending review. One provisional rate-limiting lane groups the work; no team assignments are invented.

## Ordered delivery and proof

| Step | Outcome | Completion evidence |
| --- | --- | --- |
| 1. Schema | Versioned policy rejects invalid limits and windows | Valid policy accepted; invalid limits/windows and unsupported versions rejected |
| 2. Resolution | Exactly one effective policy for an organization | Deterministic resolution, organization isolation, reviewed missing/conflict behavior |
| 3. Enforcement | First 100 requests allowed; request 101 denied in the same window | Controlled-clock boundary test, isolation and window behavior |
| 4. Decision and integration proof | Stable denial reason and matching decision telemetry | Composed real components demonstrate the complete sequence and matching response/event fields |

Each step depends on its predecessor. The final proof consumes all preceding components and independently checks the complete steel thread. Each leaf has a separate proposed write surface and observable completion; downstream proof still requires upstream inputs.

## Open issues before approval

- Identify the accountable in-scope owner.
- Specify supported schema versions, resolution precedence/defaults and missing/conflict handling, exact window semantics, and stable denial/telemetry fields.
- Confirm the implementation target, language, test harness and exact paths. The recipe's source directories and behavioral test commands are proposed future surfaces; this fixture repository has no implementation or those tests.

These are open review objections. Production storage and deployment choices are deferred outside this proposal's scope.

## Artifacts and validation

The authored recipe is `plans/rate-limiting/recipe.yaml`; it pins the exact blueprint SHA-256. Native preparation reached `DELIVERY_PLAN=OPEN_OBJECTIONS` and refused to publish a native delivery plan. The CLI still reports `DECOMPOSE=INTENT`; only intake is persisted under `tasks/.plans/rate-limiting`. The authored proposal and recipe remain available here for review. Open issues were preserved rather than marked resolved. No compiled task graph exists.

This was planning validation only. Behavioral evaluations were not run, and feature behavior remains unproven.

Next action: inspect the proposal and resolve the recorded objections when review is requested. This request ends at proposal; do not approve, compile, materialize, sign, run, accept, commit or publish.
