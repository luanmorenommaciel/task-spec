---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-POLICY-RESOLUTION
seam_id: SEAM-POLICY
swimlane_id: LANE-POLICY
observable_state: Resolution returns exactly one effective policy for an organization, or a typed no-policy
  result, and never an ambiguous set.
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
    overlapping, and duplicate-precedence policy sets, returns a typed no-policy result when none applies,
    is deterministic under input reordering, and its tests pass.
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
    then: exactly one policy is returned, chosen by deterministic precedence that is stable under input
      reordering
  - id: B-2
    given: no policy that applies to the organization
    when: the effective policy is resolved
    then: a typed no-policy result is returned rather than a default limit, an empty collection, or an
      exception
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
    reason: The steel thread requires exactly one effective policy; pushing the choice to callers makes
      precedence unprovable here.
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
source_seam_sha256: 2d790e947260e6cd71ea2576f3ec6803dad3363174dccf167435b69a83345cd0
---
# Resolution returns exactly one effective policy for an organization, or a typed no-policy result, and never an ambiguous set.

## Observable proof

Resolution tests over absent, single, overlapping, and duplicate-precedence policy sets asserting exactly one effective policy or a typed no-policy result.

## Runnable leaves

- `T-20260915-policy-resolution` — Resolve exactly one effective policy per organization: The resolver returns exactly one effective policy for an organization under single, overlapping, and duplicate-precedence policy sets, returns a typed no-policy result when none applies, is deterministic under input reordering, and its tests pass.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
