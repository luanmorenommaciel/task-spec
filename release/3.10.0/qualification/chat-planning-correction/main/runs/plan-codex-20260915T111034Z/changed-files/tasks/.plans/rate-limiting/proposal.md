# Rate-limiting steel thread — proposed plan

Status: **PROPOSED, BLOCKED for preparation/review; unapproved and unexecuted.**

## Source and boundary

Source: `tests/fixtures/toolkit/blueprint.md`. Its exact SHA-256 and capture time are recorded in `recipe.json`; the original text is preserved in `intake.md`. The source is a synthetic evidence fixture, not evidence of shipped behavior.

Usage metering stays **provider-owned and out of scope**. Local counters support request admission only; decision telemetry must not become a billable usage ledger. Production storage and deployment infrastructure remain unselected and outside this plan.

The blueprint does not name a rate-limiting owner. The proposed lane and seam therefore explicitly retain an unassigned owner. A future reviewer does not automatically become that owner.

## Proposed sequence

| Step | Outcome and completion evidence | Depends on |
| --- | --- | --- |
| 1. Versioned policy | Accept valid policies; reject invalid limits/windows and unsupported versions with deterministic errors. | None |
| 2. Organization resolution | Return exactly one validated effective policy for an organization; test missing/ambiguous input and organization isolation. | 1 |
| 3. Enforcement | Allow requests 1–100 and deny request 101 in the same window; test counter isolation and proposed window boundary semantics with an injected clock. | 2 |
| 4. Denial and telemetry | Return a stable denial reason and a matching decision event; drive the actual components through all 101 requests and assert no provider metering interactions. | 1, 2, 3 |

One responsibility lane contains four capability legs. Each leaf has a bounded output and assessable completion; downstream verification still requires its declared inputs. The final leaf proves the whole composed steel thread. No separate owners or SDLC lanes are inferred from the four source steps.

## Proposed implementation and verification

`recipe.json` specifies four M-sized leaves, disjoint proposed source/test files, dependencies, behaviors and three proposed test commands per leaf. The candidate implementation uses Python standard-library tests and an in-memory fixture. These are proposal details, not an existing stack or executed tests. No source code or tests are implemented by this planning request.

All eventual leaf verification must include its own behavior assertions. Final integration proof must use the real preceding components; mocked upstream behavior or the existence of this blueprint is insufficient proof.

## Open decisions

1. Assign the responsible rate-limiting owner; preserve provider ownership of metering.
2. Decide policy precedence/defaults and missing/ambiguous configuration behavior. Explicit configuration errors are proposed.
3. Decide window semantics and the public denial/telemetry contract. Fixed windows, `rate_limit_exceeded`, and matching organization/policy/request fields are proposed.
4. Confirm the implementation location/runtime and local verification harness. Production infrastructure is a separate future decision outside this initiative.

These remain `OPEN` objections and `system_map.unknowns` in the native recipe. They must not be silently converted to accepted risk to pass validation.

## Lifecycle and next action

Preparation reported `unaccepted_decision`; native initiative state remains `INTENT` with no generated delivery plan. See `validation.md` for the exact checks. The authored proposal and recipe are preserved for review.

This artifact requests no approval and grants no execution authority. The smallest next action is to identify the responsible rate-limiting owner, then resolve the contract/harness decisions and prepare a revised proposal. Review, compilation, task materialization, sealing, execution and acceptance have not been performed.
