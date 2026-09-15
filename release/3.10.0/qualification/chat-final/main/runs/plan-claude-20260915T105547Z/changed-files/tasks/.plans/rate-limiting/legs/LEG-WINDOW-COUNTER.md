---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-WINDOW-COUNTER
seam_id: SEAM-ENFORCEMENT
swimlane_id: LANE-ENFORCEMENT
observable_state: Per-organization, per-window request counts increment behind a storage port and reset
  at window boundaries under an injected clock.
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
  goal: Provide a counter port plus an in-memory adapter that tracks request counts per organization and
    window under an injected clock, without selecting a production store.
  done_condition: A counter port interface and in-memory adapter increment and read counts keyed by organization
    and window start, reset when the injected clock crosses a window boundary, keep organizations isolated,
    and their tests pass; no production storage dependency is added.
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
    description: Counts increment per organization and stay isolated between organizations within one
      window.
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
source_seam_sha256: 5a38e7f8e7f38c997ac61e0a48f82e91cecf459334485da81eafc1f340d5a306
---
# Per-organization, per-window request counts increment behind a storage port and reset at window boundaries under an injected clock.

## Observable proof

Counter tests driving an injected clock across a window boundary and across two organizations.

## Runnable leaves

- `T-20260915-window-counter` — Window counter behind a storage port: A counter port interface and in-memory adapter increment and read counts keyed by organization and window start, reset when the injected clock crosses a window boundary, keep organizations isolated, and their tests pass; no production storage dependency is added.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
