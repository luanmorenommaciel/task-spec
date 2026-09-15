---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-DENIAL-REASON
seam_id: SEAM-DECISION-SIGNAL
swimlane_id: LANE-SIGNAL
observable_state: A denial carries a stable enumerated reason code, and any change to the enumeration
  fails a golden snapshot test.
proof: Reason tests asserting the denial reason value plus a golden snapshot of the reason enumeration.
requires:
- admission decision function
produces:
- reason enumeration
- reason tests
tasks:
- id: T-20260915-denial-reason
  title: Stable enumerated denial reason
  goal: Introduce a stable reason enumeration and attach the rate-limit-exceeded reason to denial decisions,
    with change detection on the enumeration.
  done_condition: Denials carry a stable enumerated reason code, the reason value is asserted by tests,
    a golden snapshot test fails if the enumeration changes, and the module tests pass.
  effort: M
  profile: standard
  execution_backend: claude
  required_tools:
  - bash
  - python3
  - pytest
  depends_on:
  - T-20260915-admission-decision
  touches_paths:
  - src/rate_limiting/limiter.py
  creates_paths:
  - src/rate_limiting/reasons.py
  - tests/rate_limiting/test_denial_reason.py
  behavior:
  - id: B-1
    given: a request denied because the window limit is exhausted
    when: the decision is inspected
    then: it carries the enumerated rate-limit-exceeded reason code with a stable string value
  - id: B-2
    given: the reason enumeration and its golden snapshot
    when: a code or value in the enumeration is added, removed, or renamed
    then: the snapshot test fails until the change is made deliberately
  evals:
  - id: eval_1
    description: A denial carries the enumerated rate-limit-exceeded reason.
    bash: python3 -m pytest tests/rate_limiting/test_denial_reason.py -q -k reason_code
    verifies:
    - B-1
  - id: eval_2
    description: The reason enumeration matches its golden snapshot.
    bash: python3 -m pytest tests/rate_limiting/test_denial_reason.py -q -k snapshot
    verifies:
    - B-2
  - id: eval_3
    description: The whole denial reason test module passes.
    bash: python3 -m pytest tests/rate_limiting/test_denial_reason.py -q
    verifies:
    - B-1
    - B-2
  anti_patterns:
  - action: Deriving the reason string from an exception message or class name.
    reason: Refactors then silently change a value the source requires to be stable.
    instead: Define the code explicitly in the enumeration and assert its literal value.
  - action: Localizing or templating the reason code with request-specific text.
    reason: A machine-readable reason must not vary per request or locale.
    instead: Keep the code stable and put any variable context in separate decision fields.
  - action: Changing the allow/deny boundary while wiring the reason into the limiter.
    reason: That is the admission leaf's sealed outcome, and editing it here would invalidate its proof.
    instead: Attach the reason to the existing decision value without altering when denial occurs.
  do_not_touch:
  - tests/rate_limiting/test_admission_decision.py
  - any provider usage metering client, record, or schema
  - production storage or deployment configuration
  rollback: Revert the limiter edit and delete the reason module and test file.
  shared_resources:
  - src/rate_limiting/limiter.py
  execution_recipe: test-first
  sdlc_stages:
  - build
  - test
source_seam_sha256: 6ec9723980d779da4c55ef15d73cb850f61bf5ba93f02a8930abedf7454577d6
---
# A denial carries a stable enumerated reason code, and any change to the enumeration fails a golden snapshot test.

## Observable proof

Reason tests asserting the denial reason value plus a golden snapshot of the reason enumeration.

## Runnable leaves

- `T-20260915-denial-reason` — Stable enumerated denial reason: Denials carry a stable enumerated reason code, the reason value is asserted by tests, a golden snapshot test fails if the enumeration changes, and the module tests pass.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
