---
schema_version: 1
kind: seam
claim: derived
id: SEAM-ENFORCEMENT
name: Windowed admission decision
description: Owns per-window request counting and the allow or deny decision against the effective policy.
evidence:
- EV-BLUEPRINT
- EV-METERING-BOUNDARY
responsibility: Count requests per organization and window behind a storage port and decide whether a
  request is admitted.
consumes:
- effective policy
- request events
- injected clock
produces:
- storage port
- in-memory counter adapter
- admission decision
owner: UNASSIGNED placeholder (see DEC-OWNER-UNASSIGNED)
independent_proof: Deny-on-101 is provable with an injected clock and the in-memory counter adapter, without
  telemetry, a production store, or metering.
decision_ids:
- DEC-METERING-OUT-OF-SCOPE
- DEC-NO-INFRA-SELECTION
rejected_alternatives:
- alternative: Count requests from provider usage metering records.
  reason: Metering is provider-owned and out of scope; the limiter must own its own counter to keep this
    seam independently provable.
- alternative: Select a production counter store such as Redis now.
  reason: The source defers production storage and deployment selection, so the counter stays behind a
    port with an in-memory adapter.
swimlane:
  id: LANE-ENFORCEMENT
  name: Enforcement lane
  owner: UNASSIGNED placeholder (see DEC-OWNER-UNASSIGNED)
  legs:
  - id: LEG-WINDOW-COUNTER
    observable_state: Per-organization, per-window request counts increment behind a storage port and
      reset at window boundaries under an injected clock.
    proof: Counter tests driving an injected clock across a window boundary and across two organizations.
    requires:
    - effective policy
    produces:
    - storage port
    - in-memory counter adapter
    - counter tests
    tasks:
    - id: T-20260915-window-counter
      title: Window counter behind a storage port
      goal: Provide a counter port plus an in-memory adapter that tracks request counts per organization
        and window under an injected clock, without selecting a production store.
      done_condition: A counter port interface and in-memory adapter increment and read counts keyed by
        organization and window start, reset when the injected clock crosses a window boundary, keep organizations
        isolated, and their tests pass; no production storage dependency is added.
      effort: M
      profile: standard
      execution_backend: claude
      required_tools:
      - bash
      - python3
      - pytest
      depends_on:
      - T-20260915-policy-resolution
      touches_paths: []
      creates_paths:
      - src/rate_limiting/counter_port.py
      - src/rate_limiting/memory_counter.py
      - tests/rate_limiting/test_window_counter.py
      behavior:
      - id: B-1
        given: an in-memory counter and an injected clock held inside one window
        when: requests are recorded for an organization
        then: the count for that organization and window increments by one per request and other organizations
          stay at zero
      - id: B-2
        given: a counter with recorded requests in the current window
        when: the injected clock advances past the window boundary
        then: the count read for the new window starts at zero while the port interface stays unchanged
      evals:
      - id: eval_1
        description: Counts increment per organization and stay isolated between organizations within
          one window.
        bash: python3 -m pytest tests/rate_limiting/test_window_counter.py -q -k increment
        verifies:
        - B-1
      - id: eval_2
        description: Crossing a window boundary with the injected clock resets the observed count.
        bash: python3 -m pytest tests/rate_limiting/test_window_counter.py -q -k boundary
        verifies:
        - B-2
      - id: eval_3
        description: The whole counter test module passes.
        bash: python3 -m pytest tests/rate_limiting/test_window_counter.py -q
        verifies:
        - B-1
        - B-2
      anti_patterns:
      - action: Adding a Redis, database, or other production store dependency.
        reason: Production storage and deployment infrastructure are explicitly not selected by this plan.
        instead: Define the port and ship only the in-memory adapter used by tests.
      - action: Reading wall-clock time directly inside the counter.
        reason: An ambient clock makes window boundaries untestable and the deny-on-101 proof flaky.
        instead: Take the clock as an injected dependency supplied by the caller and tests.
      - action: Sourcing counts from provider usage metering.
        reason: Metering is provider-owned and out of scope; a metering-backed counter would move enforcement
          across the ownership boundary.
        instead: Keep the counter state owned by this component behind its own port.
      do_not_touch:
      - src/rate_limiting/policy_schema.py
      - src/rate_limiting/policy_resolver.py
      - any provider usage metering client, record, or schema
      rollback: Delete the created port, adapter, and test file; no existing code is modified.
      shared_resources:
      - src/rate_limiting/counter_port.py
      execution_recipe: test-first
      sdlc_stages:
      - design
      - build
      - test
  - id: LEG-ADMISSION-DECISION
    observable_state: With a limit of 100 in one window, the first 100 requests are allowed and request
      101 is denied.
    proof: A sequence test issuing 101 requests against a limit of 100 within one window and asserting
      the allow/deny boundary.
    requires:
    - effective policy
    - storage port
    produces:
    - admission decision function
    - decision tests
    tasks:
    - id: T-20260915-admission-decision
      title: Allow the first 100 requests and deny request 101
      goal: Combine the effective policy and the window counter into an admission decision that allows
        requests up to the limit and denies the request that exceeds it.
      done_condition: The limiter returns an allow decision for requests 1 through 100 and a deny decision
        for request 101 against a limit of 100 in one window, denies without incrementing the admitted
        count, handles the typed no-policy result explicitly, and its tests pass.
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
        reason: It makes the limit off-by-one across windows and corrupts the deny boundary the source
          fixes at request 101.
        instead: Increment only on admission and assert the count after the denial.
      - action: Treating the typed no-policy result as an implicit allow or deny.
        reason: An implicit branch hides an unresolved product decision behind enforcement behavior.
        instead: Handle the no-policy result explicitly and surface it as its own outcome for review.
      - action: Emitting telemetry or formatting user-facing reason text here.
        reason: The denial reason and decision telemetry are owned by the decision-signal seam and must
          stay independently provable.
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
---
# Windowed admission decision

Owns per-window request counting and the allow or deny decision against the effective policy.

## Responsibility

Count requests per organization and window behind a storage port and decide whether a request is admitted.

## Independent proof

Deny-on-101 is provable with an injected clock and the in-memory counter adapter, without telemetry, a production store, or metering.

## Rejected alternatives

- **Count requests from provider usage metering records.** — Metering is provider-owned and out of scope; the limiter must own its own counter to keep this seam independently provable.
- **Select a production counter store such as Redis now.** — The source defers production storage and deployment selection, so the counter stays behind a port with an in-memory adapter.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
