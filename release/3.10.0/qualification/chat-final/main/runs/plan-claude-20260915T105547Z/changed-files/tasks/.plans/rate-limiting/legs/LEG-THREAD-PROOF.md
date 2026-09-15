---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-THREAD-PROOF
seam_id: SEAM-THREAD-PROOF
swimlane_id: LANE-THREAD-PROOF
observable_state: 'One end-to-end test walks the source order: invalid policy rejected, exactly one effective
  policy resolved, request 101 denied after 100 allowed, stable reason returned with matching telemetry.'
proof: The steel thread integration test passes and fails when any step of the thread regresses.
requires:
- policy resolver
- admission decision function
- reason enumeration
- telemetry emitter
produces:
- steel thread integration test
tasks:
- id: T-20260915-steel-thread-proof
  title: End-to-end steel thread proof in source order
  goal: Prove the composed four-step steel thread with one integration test that exercises the components
    together in the order stated by the source.
  done_condition: One integration test rejects an invalid policy, resolves exactly one effective policy
    for an organization, allows 100 requests and denies request 101 in the same window, and asserts the
    stable reason with a matching telemetry record; it passes and no production module is modified by
    this leaf.
  effort: S
  profile: standard
  execution_backend: claude
  required_tools:
  - bash
  - python3
  - pytest
  depends_on:
  - T-20260915-decision-telemetry
  touches_paths: []
  creates_paths:
  - tests/rate_limiting/test_steel_thread.py
  behavior:
  - id: B-1
    given: a validated policy set, an in-memory counter, an injected clock, and a fake telemetry sink
    when: an invalid policy is validated and then 101 requests are evaluated in one window against a resolved
      limit of 100
    then: the invalid policy is rejected, exactly one effective policy is resolved, requests 1 to 100
      are allowed, and request 101 is denied
  - id: B-2
    given: the denial produced by that same run
    when: the returned decision and the collected telemetry record are compared
    then: the stable reason code appears in both and the telemetry record matches the returned decision
  evals:
  - id: eval_1
    description: The ordered steel thread from schema rejection through denial holds end to end.
    bash: python3 -m pytest tests/rate_limiting/test_steel_thread.py -q -k thread
    verifies:
    - B-1
  - id: eval_2
    description: The denial reason and the emitted telemetry agree in the composed run.
    bash: python3 -m pytest tests/rate_limiting/test_steel_thread.py -q -k telemetry
    verifies:
    - B-2
  - id: eval_3
    description: The full rate-limiting suite passes with the integration test included.
    bash: python3 -m pytest tests/rate_limiting -q
    verifies:
    - B-1
    - B-2
  anti_patterns:
  - action: Editing production modules to make the integration test pass.
    reason: This leaf proves composition; repairing behavior here hides which sealed leaf actually regressed.
    instead: Report the failing step and repair it in the owning leaf under its own authorization.
  - action: Substituting mocks for the policy resolver, counter, or limiter.
    reason: Mocking the components under proof makes the composed thread untested.
    instead: Use the real modules with only the clock and telemetry sink injected.
  - action: Asserting only the final denial and skipping the earlier steps.
    reason: The source fixes an ordered thread; a denial-only assertion would pass with broken schema
      or resolution behavior.
    instead: Assert each of the four steps in the stated order within the one test.
  do_not_touch:
  - src/rate_limiting/policy_schema.py
  - src/rate_limiting/policy_resolver.py
  - src/rate_limiting/limiter.py
  - src/rate_limiting/telemetry.py
  - any provider usage metering client, record, or schema
  rollback: Delete the integration test file; no production module is modified.
  proves_capabilities:
  - LEG-POLICY-SCHEMA
  - LEG-POLICY-RESOLUTION
  - LEG-WINDOW-COUNTER
  - LEG-ADMISSION-DECISION
  - LEG-DENIAL-REASON
  - LEG-DECISION-TELEMETRY
  execution_recipe: test-first
  sdlc_stages:
  - test
source_seam_sha256: 88f32448321ed3332e030d82112f11abb3b425e8a300f13055a5b2a829cafa66
---
# One end-to-end test walks the source order: invalid policy rejected, exactly one effective policy resolved, request 101 denied after 100 allowed, stable reason returned with matching telemetry.

## Observable proof

The steel thread integration test passes and fails when any step of the thread regresses.

## Runnable leaves

- `T-20260915-steel-thread-proof` — End-to-end steel thread proof in source order: One integration test rejects an invalid policy, resolves exactly one effective policy for an organization, allows 100 requests and denies request 101 in the same window, and asserts the stable reason with a matching telemetry record; it passes and no production module is modified by this leaf.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
