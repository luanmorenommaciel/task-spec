---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-DECISION-TELEMETRY
seam_id: SEAM-DECISION-SIGNAL
swimlane_id: LANE-SIGNAL
observable_state: Each decision emits exactly one telemetry record whose organization, outcome, and reason
  fields match the returned decision.
proof: Telemetry tests against a fake sink asserting one record per decision and field-level agreement
  with the decision.
requires:
- reason enumeration
produces:
- telemetry emitter
- telemetry tests
tasks:
- id: T-20260915-decision-telemetry
  title: Decision telemetry matching the returned decision
  goal: Emit one decision telemetry record per admission decision through an injectable sink, with fields
    that match the decision returned to the caller.
  done_condition: Every allow and deny decision emits exactly one telemetry record through an injected
    sink whose organization, outcome, and reason fields equal the returned decision's, a sink failure
    does not change the decision, and the telemetry tests pass.
  effort: M
  profile: standard
  execution_backend: claude
  required_tools:
  - bash
  - python3
  - pytest
  depends_on:
  - T-20260915-denial-reason
  touches_paths:
  - src/rate_limiting/limiter.py
  creates_paths:
  - src/rate_limiting/telemetry.py
  - tests/rate_limiting/test_decision_telemetry.py
  behavior:
  - id: B-1
    given: a fake telemetry sink and a denied request
    when: the decision is produced
    then: exactly one record is emitted whose organization, outcome, and reason equal the returned decision's
      fields
  - id: B-2
    given: a telemetry sink that raises on emit
    when: a request is evaluated
    then: the allow or deny decision returned to the caller is unchanged and the failure is surfaced without
      being silently swallowed
  evals:
  - id: eval_1
    description: One telemetry record per decision, with fields matching the decision.
    bash: python3 -m pytest tests/rate_limiting/test_decision_telemetry.py -q -k matches
    verifies:
    - B-1
  - id: eval_2
    description: A failing sink does not alter the admission decision.
    bash: python3 -m pytest tests/rate_limiting/test_decision_telemetry.py -q -k sink_failure
    verifies:
    - B-2
  - id: eval_3
    description: The whole telemetry test module passes.
    bash: python3 -m pytest tests/rate_limiting/test_decision_telemetry.py -q
    verifies:
    - B-1
    - B-2
  anti_patterns:
  - action: Writing decision telemetry into provider usage metering records.
    reason: Metering is provider-owned and out of scope; crossing that boundary would make this plan responsible
      for someone else's data.
    instead: Emit through the injectable decision telemetry sink owned by this seam.
  - action: Recomputing the reason or outcome inside the emitter.
    reason: Recomputation lets telemetry and the returned decision disagree, which is exactly what this
      leg must rule out.
    instead: Emit fields read from the decision value produced upstream.
  - action: Adding a network transport or external telemetry backend.
    reason: Deployment infrastructure is not selected by this plan and a real transport makes the proof
      environment-dependent.
    instead: Define the sink interface and ship only the in-process implementation used by tests.
  do_not_touch:
  - src/rate_limiting/reasons.py
  - any provider usage metering client, record, or schema
  - production storage or deployment configuration
  rollback: Revert the limiter edit and delete the telemetry module and test file.
  shared_resources:
  - src/rate_limiting/limiter.py
  execution_recipe: test-first
  sdlc_stages:
  - build
  - test
source_seam_sha256: 6ec9723980d779da4c55ef15d73cb850f61bf5ba93f02a8930abedf7454577d6
---
# Each decision emits exactly one telemetry record whose organization, outcome, and reason fields match the returned decision.

## Observable proof

Telemetry tests against a fake sink asserting one record per decision and field-level agreement with the decision.

## Runnable leaves

- `T-20260915-decision-telemetry` — Decision telemetry matching the returned decision: Every allow and deny decision emits exactly one telemetry record through an injected sink whose organization, outcome, and reason fields equal the returned decision's, a sink failure does not change the decision, and the telemetry tests pass.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
