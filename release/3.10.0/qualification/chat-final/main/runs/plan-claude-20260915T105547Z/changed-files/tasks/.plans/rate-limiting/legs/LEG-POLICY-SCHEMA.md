---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-POLICY-SCHEMA
seam_id: SEAM-POLICY
swimlane_id: LANE-POLICY
observable_state: A versioned policy schema accepts valid policies and rejects invalid limits and windows
  with a typed validation error.
proof: Schema tests over a table of valid and invalid limit and window values, including a version field
  mismatch.
requires: []
produces:
- policy schema module
- policy schema tests
tasks:
- id: T-20260915-policy-schema
  title: Versioned rate-limit policy schema with validation
  goal: Define a versioned rate-limit policy structure and a validator that accepts well-formed policies
    and rejects invalid limits and windows with typed errors.
  done_condition: A policy schema module validates a versioned policy document, rejecting non-positive
    or non-integer limits, non-positive or unknown window durations, and unsupported schema versions,
    each with a typed validation error; schema tests cover valid and invalid cases and pass.
  effort: S
  profile: standard
  execution_backend: claude
  required_tools:
  - bash
  - python3
  - pytest
  depends_on: []
  touches_paths: []
  creates_paths:
  - src/rate_limiting/policy_schema.py
  - tests/rate_limiting/test_policy_schema.py
  behavior:
  - id: B-1
    given: a policy document with a supported schema version, a positive integer limit, and a supported
      window duration
    when: the policy is validated
    then: validation succeeds and returns a policy value carrying its schema version, limit, and window
  - id: B-2
    given: a policy document with a zero, negative, or non-integer limit, or a zero, negative, or unsupported
      window
    when: the policy is validated
    then: validation fails with a typed validation error naming the offending field, and no policy value
      is returned
  evals:
  - id: eval_1
    description: Valid versioned policies validate and round-trip their fields.
    bash: python3 -m pytest tests/rate_limiting/test_policy_schema.py -q -k valid
    verifies:
    - B-1
  - id: eval_2
    description: Invalid limits and windows are rejected with typed field-named errors.
    bash: python3 -m pytest tests/rate_limiting/test_policy_schema.py -q -k invalid
    verifies:
    - B-2
  - id: eval_3
    description: The whole schema test module passes.
    bash: python3 -m pytest tests/rate_limiting/test_policy_schema.py -q
    verifies:
    - B-1
    - B-2
  anti_patterns:
  - action: Accepting an unknown schema version by silently coercing it to the latest.
    reason: Silent coercion makes a versioned schema unversioned and hides policy drift.
    instead: Reject unsupported versions with the same typed validation error path as other invalid fields.
  - action: Reading limits or windows from provider usage metering.
    reason: Metering is provider-owned and out of scope for this plan.
    instead: Validate only the authored policy document passed to the validator.
  - action: Raising bare strings or generic exceptions for invalid input.
    reason: Downstream resolution and enforcement cannot branch on untyped errors, and the denial reason
      must stay stable.
    instead: Raise or return a typed validation error carrying the offending field name.
  do_not_touch:
  - tests/fixtures/toolkit/blueprint.md
  - any provider usage metering client, record, or schema
  - production storage or deployment configuration
  rollback: Delete the created module and test file; no existing code is modified.
  execution_recipe: test-first
  sdlc_stages:
  - design
  - build
  - test
source_seam_sha256: 2d790e947260e6cd71ea2576f3ec6803dad3363174dccf167435b69a83345cd0
---
# A versioned policy schema accepts valid policies and rejects invalid limits and windows with a typed validation error.

## Observable proof

Schema tests over a table of valid and invalid limit and window values, including a version field mismatch.

## Runnable leaves

- `T-20260915-policy-schema` — Versioned rate-limit policy schema with validation: A policy schema module validates a versioned policy document, rejecting non-positive or non-integer limits, non-positive or unknown window durations, and unsupported schema versions, each with a typed validation error; schema tests cover valid and invalid cases and pass.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
