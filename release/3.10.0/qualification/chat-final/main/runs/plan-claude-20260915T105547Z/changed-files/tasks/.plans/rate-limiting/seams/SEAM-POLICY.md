---
schema_version: 1
kind: seam
claim: derived
id: SEAM-POLICY
name: Policy definition and resolution
description: Owns what a rate-limit policy is, how its versions validate, and which single policy is effective
  for an organization.
evidence:
- EV-BLUEPRINT
- EV-REPO-STATE
responsibility: Turn authored policy documents into exactly one validated effective policy for an organization.
consumes:
- authored policy documents
- organization identifier
produces:
- validated versioned policy
- effective policy
owner: UNASSIGNED placeholder (see DEC-OWNER-UNASSIGNED)
independent_proof: Rejection of invalid limits and windows and single-effective-policy resolution are
  assertable from policy documents alone, with no counter, clock, or telemetry sink.
decision_ids:
- DEC-METERING-OUT-OF-SCOPE
rejected_alternatives:
- alternative: Fold policy resolution into the enforcement path.
  reason: Resolution would then only be observable through a denial, so precedence and duplicate-policy
    bugs could not be proven independently of counting.
- alternative: Derive effective limits from provider usage metering records.
  reason: Metering is provider-owned and out of scope per the source fixture; policy must be resolvable
    without reading metering.
swimlane:
  id: LANE-POLICY
  name: Policy lane
  owner: UNASSIGNED placeholder (see DEC-OWNER-UNASSIGNED)
  legs:
  - id: LEG-POLICY-SCHEMA
    observable_state: A versioned policy schema accepts valid policies and rejects invalid limits and
      windows with a typed validation error.
    proof: Schema tests over a table of valid and invalid limit and window values, including a version
      field mismatch.
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
        given: a policy document with a zero, negative, or non-integer limit, or a zero, negative, or
          unsupported window
        when: the policy is validated
        then: validation fails with a typed validation error naming the offending field, and no policy
          value is returned
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
        instead: Reject unsupported versions with the same typed validation error path as other invalid
          fields.
      - action: Reading limits or windows from provider usage metering.
        reason: Metering is provider-owned and out of scope for this plan.
        instead: Validate only the authored policy document passed to the validator.
      - action: Raising bare strings or generic exceptions for invalid input.
        reason: Downstream resolution and enforcement cannot branch on untyped errors, and the denial
          reason must stay stable.
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
  - id: LEG-POLICY-RESOLUTION
    observable_state: Resolution returns exactly one effective policy for an organization, or a typed
      no-policy result, and never an ambiguous set.
    proof: Resolution tests over absent, single, overlapping, and duplicate-precedence policy sets asserting
      exactly one effective policy or a typed no-policy result.
    requires:
    - policy schema module
    produces:
    - effective policy
    - policy resolver
    - policy resolver tests
    tasks:
    - id: T-20260915-policy-resolution
      title: Resolve exactly one effective policy per organization
      goal: Resolve a set of validated policies to exactly one effective policy for a given organization,
        with deterministic precedence and a typed result when no policy applies.
      done_condition: The resolver returns exactly one effective policy for an organization under single,
        overlapping, and duplicate-precedence policy sets, returns a typed no-policy result when none
        applies, is deterministic under input reordering, and its tests pass.
      effort: S
      profile: standard
      execution_backend: claude
      required_tools:
      - bash
      - python3
      - pytest
      depends_on:
      - T-20260915-policy-schema
      touches_paths: []
      creates_paths:
      - src/rate_limiting/policy_resolver.py
      - tests/rate_limiting/test_policy_resolver.py
      behavior:
      - id: B-1
        given: several validated policies that could apply to one organization
        when: the effective policy is resolved for that organization
        then: exactly one policy is returned, chosen by deterministic precedence that is stable under
          input reordering
      - id: B-2
        given: no policy that applies to the organization
        when: the effective policy is resolved
        then: a typed no-policy result is returned rather than a default limit, an empty collection, or
          an exception
      evals:
      - id: eval_1
        description: Overlapping and duplicate policy sets resolve to exactly one effective policy, stable
          under reordering.
        bash: python3 -m pytest tests/rate_limiting/test_policy_resolver.py -q -k effective
        verifies:
        - B-1
      - id: eval_2
        description: An organization with no applicable policy yields a typed no-policy result.
        bash: python3 -m pytest tests/rate_limiting/test_policy_resolver.py -q -k no_policy
        verifies:
        - B-2
      - id: eval_3
        description: The whole resolver test module passes.
        bash: python3 -m pytest tests/rate_limiting/test_policy_resolver.py -q
        verifies:
        - B-1
        - B-2
      anti_patterns:
      - action: Returning a list of candidate policies and letting the caller pick.
        reason: The steel thread requires exactly one effective policy; pushing the choice to callers
          makes precedence unprovable here.
        instead: Return one effective policy or a typed no-policy result from the resolver itself.
      - action: Substituting a hardcoded default limit when no policy applies.
        reason: A hidden default turns a missing-policy condition into a silent enforcement decision.
        instead: Return the typed no-policy result and let the enforcement leaf decide how to treat it.
      - action: Re-validating or redefining policy fields inside the resolver.
        reason: Duplicated validation drifts from the schema leaf and breaks its independent proof.
        instead: Consume already-validated policy values from the policy schema module.
      do_not_touch:
      - src/rate_limiting/policy_schema.py
      - any provider usage metering client, record, or schema
      - production storage or deployment configuration
      rollback: Delete the created resolver and test file; no existing code is modified.
      execution_recipe: test-first
      sdlc_stages:
      - build
      - test
---
# Policy definition and resolution

Owns what a rate-limit policy is, how its versions validate, and which single policy is effective for an organization.

## Responsibility

Turn authored policy documents into exactly one validated effective policy for an organization.

## Independent proof

Rejection of invalid limits and windows and single-effective-policy resolution are assertable from policy documents alone, with no counter, clock, or telemetry sink.

## Rejected alternatives

- **Fold policy resolution into the enforcement path.** — Resolution would then only be observable through a denial, so precedence and duplicate-policy bugs could not be proven independently of counting.
- **Derive effective limits from provider usage metering records.** — Metering is provider-owned and out of scope per the source fixture; policy must be resolvable without reading metering.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
