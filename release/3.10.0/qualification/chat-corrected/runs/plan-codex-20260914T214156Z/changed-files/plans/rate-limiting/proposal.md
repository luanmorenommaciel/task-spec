# Proposed rate-limiting steel thread

Status: **proposed, unapproved, unexecuted**. Source: [blueprint](../../tests/fixtures/toolkit/blueprint.md). The authored [TaskSpec recipe](recipe.yaml) retains the source SHA-256 and proposed task contracts. This synthetic fixture describes desired behavior; it does not establish shipped behavior.

Usage metering remains **provider-owned and out of scope**. Enforcement may maintain request-window state and emit decision telemetry, but must not aggregate provider usage, create billing records, or take over metering. Production storage and deployment infrastructure remain unselected.

The source names no responsible owner for the in-scope work. Ownership is explicitly unassigned; this proposal does not invent teams or assign the work to the metering provider. One proposed rate-limiting responsibility boundary contains four sequential outcomes.

| Step | Observable completion | Dependencies | Proposed new files |
| --- | --- | --- | --- |
| 1. Versioned policy schema | Valid limits and windows pass; invalid values and unsupported versions are rejected. | None | `rate_limiting/policy_schema.py`, `tests/rate_limiting/test_policy_schema.py` |
| 2. Organization resolution | Exactly one validated effective policy is returned for the organization. Missing or ambiguous candidates produce explicit errors under the proposed fixture contract. | Step 1 | `rate_limiting/policy_resolution.py`, `tests/rate_limiting/test_policy_resolution.py` |
| 3. Request enforcement | Requests 1–100 are allowed in one controlled window; request 101 is denied. Check organization isolation and window reset. | Step 2 | `rate_limiting/request_enforcement.py`, `tests/rate_limiting/test_request_enforcement.py` |
| 4. Denial and decision telemetry | The full chain returns a stable denial reason for request 101 and emits matching telemetry for that organization and request. | Steps 1–3 | `rate_limiting/denial_telemetry.py`, `tests/rate_limiting/test_denial_telemetry.py` |

Each step has an independently assessable result and a bounded write scope. Independence of completion does not imply independence of inputs: downstream checks consume the declared upstream outputs. Step 4 owns the full-chain integration proof; completing earlier steps alone does not prove the complete capability.

The recipe proposes a local Python fixture with an injected clock, in-memory enforcement state and an event collector. These paths and design choices are proposals, not existing implementation or production infrastructure selections. Proposed eval commands refer to future tests and have not been run. Full-chain checks must exercise the implementations, compare denial and telemetry, and confirm that no provider metering calls or records occur.

Before native review, resolve the responsible owner and review the proposed policy-resolution error behavior, supported versions and value rules, window semantics, and stable denial/event fields. Production storage and deployment choices remain outside this proposal.

TaskSpec intake was initialized as `rate-limiting`. A dry-run prepare reported `unaccepted_decision` because the recipe explicitly retains unresolved ownership and fixture-contract decisions. No native delivery plan was prepared, reviewed, compiled, materialized, signed, or executed. The reviewable draft is this document and its recipe; deterministic preparation cannot supply missing ownership or product decisions.

The smallest next action is to supply the in-scope owner and resolve the recorded design decisions in the draft. A later authorized preparation can then generate the native topology for review. This request ends at the proposal stage.
