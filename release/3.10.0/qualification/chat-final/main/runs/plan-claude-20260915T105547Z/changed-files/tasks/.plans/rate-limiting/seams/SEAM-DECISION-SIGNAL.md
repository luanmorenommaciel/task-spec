---
schema_version: 1
kind: seam
claim: derived
id: SEAM-DECISION-SIGNAL
name: Denial reason and decision telemetry
description: Owns the stable machine-readable denial reason and the telemetry record emitted for each
  decision.
evidence:
- EV-BLUEPRINT
- EV-METERING-BOUNDARY
responsibility: Give every decision a stable enumerated reason and emit exactly one matching decision
  telemetry record.
consumes:
- admission decision
produces:
- stable reason enumeration
- decision telemetry record
owner: UNASSIGNED placeholder (see DEC-OWNER-UNASSIGNED)
independent_proof: Reason stability and telemetry agreement are assertable from decision values against
  a fake sink, with no network, no store, and no metering pipeline.
decision_ids:
- DEC-METERING-OUT-OF-SCOPE
- DEC-NO-INFRA-SELECTION
rejected_alternatives:
- alternative: Emit decision telemetry into the provider usage metering pipeline.
  reason: Metering is provider-owned and out of scope; decision telemetry is a separate signal owned by
    this seam.
- alternative: Format the denial reason as free text at each call site.
  reason: Free text cannot be asserted as stable across revisions, and the source requires a stable reason.
swimlane:
  id: LANE-SIGNAL
  name: Decision signal lane
  owner: UNASSIGNED placeholder (see DEC-OWNER-UNASSIGNED)
  legs:
  - id: LEG-DENIAL-REASON
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
      goal: Introduce a stable reason enumeration and attach the rate-limit-exceeded reason to denial
        decisions, with change detection on the enumeration.
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
        reason: That is the admission leaf's sealed outcome, and editing it here would invalidate its
          proof.
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
  - id: LEG-DECISION-TELEMETRY
    observable_state: Each decision emits exactly one telemetry record whose organization, outcome, and
      reason fields match the returned decision.
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
      goal: Emit one decision telemetry record per admission decision through an injectable sink, with
        fields that match the decision returned to the caller.
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
        then: exactly one record is emitted whose organization, outcome, and reason equal the returned
          decision's fields
      - id: B-2
        given: a telemetry sink that raises on emit
        when: a request is evaluated
        then: the allow or deny decision returned to the caller is unchanged and the failure is surfaced
          without being silently swallowed
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
        reason: Metering is provider-owned and out of scope; crossing that boundary would make this plan
          responsible for someone else's data.
        instead: Emit through the injectable decision telemetry sink owned by this seam.
      - action: Recomputing the reason or outcome inside the emitter.
        reason: Recomputation lets telemetry and the returned decision disagree, which is exactly what
          this leg must rule out.
        instead: Emit fields read from the decision value produced upstream.
      - action: Adding a network transport or external telemetry backend.
        reason: Deployment infrastructure is not selected by this plan and a real transport makes the
          proof environment-dependent.
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
---
# Denial reason and decision telemetry

Owns the stable machine-readable denial reason and the telemetry record emitted for each decision.

## Responsibility

Give every decision a stable enumerated reason and emit exactly one matching decision telemetry record.

## Independent proof

Reason stability and telemetry agreement are assertable from decision values against a fake sink, with no network, no store, and no metering pipeline.

## Rejected alternatives

- **Emit decision telemetry into the provider usage metering pipeline.** — Metering is provider-owned and out of scope; decision telemetry is a separate signal owned by this seam.
- **Format the denial reason as free text at each call site.** — Free text cannot be asserted as stable across revisions, and the source requires a stable reason.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
