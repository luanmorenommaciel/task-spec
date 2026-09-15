---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-ADMISSION-DECISION
seam_id: SEAM-ENFORCEMENT
swimlane_id: LANE-ENFORCEMENT
observable_state: With a limit of 100 in one window, the first 100 requests are allowed and request 101
  is denied.
proof: A sequence test issuing 101 requests against a limit of 100 within one window and asserting the
  allow/deny boundary.
requires:
- effective policy
- storage port
produces:
- admission decision function
- decision tests
tasks:
- id: T-20260915-admission-decision
  title: Allow the first 100 requests and deny request 101
  goal: Combine the effective policy and the window counter into an admission decision that allows requests
    up to the limit and denies the request that exceeds it.
  done_condition: The limiter returns an allow decision for requests 1 through 100 and a deny decision
    for request 101 against a limit of 100 in one window, denies without incrementing the admitted count,
    handles the typed no-policy result explicitly, and its tests pass.
  effort: S
  profile: standard
  execution_backend: claude
  required_tools:
  - bash
  - python3
  - pytest
  depends_on:
  - T-20260915-window-counter
  touches_paths: []
  creates_paths:
  - src/rate_limiting/limiter.py
  - tests/rate_limiting/test_admission_decision.py
  behavior:
  - id: B-1
    given: an effective policy with a limit of 100 for an organization and an empty window
    when: 100 requests are evaluated in that window
    then: every decision is allow and the recorded count reaches exactly 100
  - id: B-2
    given: 100 already-allowed requests in the same window
    when: request 101 is evaluated
    then: the decision is deny and the admitted count remains 100
  evals:
  - id: eval_1
    description: The first 100 requests in the window are allowed.
    bash: python3 -m pytest tests/rate_limiting/test_admission_decision.py -q -k allowed
    verifies:
    - B-1
  - id: eval_2
    description: Request 101 is denied and does not increase the admitted count.
    bash: python3 -m pytest tests/rate_limiting/test_admission_decision.py -q -k denied
    verifies:
    - B-2
  - id: eval_3
    description: The whole admission decision test module passes.
    bash: python3 -m pytest tests/rate_limiting/test_admission_decision.py -q
    verifies:
    - B-1
    - B-2
  anti_patterns:
  - action: Counting a denied request as consumed.
    reason: It makes the limit off-by-one across windows and corrupts the deny boundary the source fixes
      at request 101.
    instead: Increment only on admission and assert the count after the denial.
  - action: Treating the typed no-policy result as an implicit allow or deny.
    reason: An implicit branch hides an unresolved product decision behind enforcement behavior.
    instead: Handle the no-policy result explicitly and surface it as its own outcome for review.
  - action: Emitting telemetry or formatting user-facing reason text here.
    reason: The denial reason and decision telemetry are owned by the decision-signal seam and must stay
      independently provable.
    instead: Return a decision value and let the signal seam attach the stable reason and emit telemetry.
  do_not_touch:
  - src/rate_limiting/memory_counter.py
  - src/rate_limiting/policy_resolver.py
  - any provider usage metering client, record, or schema
  rollback: Delete the created limiter and test file; no existing code is modified.
  shared_resources:
  - src/rate_limiting/limiter.py
  execution_recipe: test-first
  sdlc_stages:
  - build
  - test
source_seam_sha256: 5a38e7f8e7f38c997ac61e0a48f82e91cecf459334485da81eafc1f340d5a306
---
# With a limit of 100 in one window, the first 100 requests are allowed and request 101 is denied.

## Observable proof

A sequence test issuing 101 requests against a limit of 100 within one window and asserting the allow/deny boundary.

## Runnable leaves

- `T-20260915-admission-decision` — Allow the first 100 requests and deny request 101: The limiter returns an allow decision for requests 1 through 100 and a deny decision for request 101 against a limit of 100 in one window, denies without incrementing the admitted count, handles the typed no-policy result explicitly, and its tests pass.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
