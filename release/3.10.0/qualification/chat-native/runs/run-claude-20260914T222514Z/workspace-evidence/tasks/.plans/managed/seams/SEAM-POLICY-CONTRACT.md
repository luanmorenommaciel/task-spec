---
schema_version: 1
kind: seam
claim: derived
id: SEAM-POLICY-CONTRACT
name: Policy contract
description: Separates accepted policy shape from resolution and enforcement.
evidence:
- E-BLUEPRINT
responsibility: Own the completion artifact
consumes:
- authored organization policy
produces:
- completed artifact
owner: platform-contracts
independent_proof: Read the artifact and independently check its exact bytes.
decision_ids:
- ADR-RATE-LIMIT-ORDER
rejected_alternatives:
- alternative: Treat the API handler as the policy boundary
  reason: Handler ownership would mix contract, resolution, and enforcement concerns.
swimlane:
  id: LANE-POLICY-CONTRACT
  name: Policy contract lane
  owner: platform-contracts
  legs:
  - id: LEG-POLICY-SCHEMA-VALID
    observable_state: The completion artifact contains its accepted value
    proof: Exact output and untouched sibling checks pass.
    requires: []
    produces:
    - completed artifact
    tasks:
    - id: T-20260914-chat-output
      title: Complete the output artifact
      goal: Write the accepted completion value inside one file.
      done_condition: a.txt contains completed and b.txt remains empty.
      effort: S
      profile: standard
      execution_backend: any
      required_tools:
      - bash
      depends_on: []
      touches_paths:
      - a.txt
      creates_paths: []
      behavior:
      - id: B-1
        given: a policy with a positive limit and window
        when: the document is validated
        then: schema validation succeeds
      - id: B-2
        given: a policy with a zero limit or window
        when: the document is validated
        then: schema validation fails
      evals:
      - id: eval_1
        description: The policy schema exists and parses as JSON
        bash: test "$(cat a.txt)" = completed
        verifies:
        - B-1
      - id: eval_2
        description: Valid policy examples pass the schema tests
        bash: test "$(wc -c < a.txt | tr -d ' ')" = 9
        verifies:
        - B-1
      - id: eval_3
        description: Invalid non-positive values are rejected
        bash: test ! -s b.txt
        verifies:
        - B-2
      anti_patterns:
      - action: encode limits only in handler constants
        reason: downstream resolution would have no versioned contract
        instead: validate one explicit schema before resolution
      - action: accept zero or negative windows
        reason: enforcement semantics would be undefined
        instead: reject non-positive values at the contract boundary
      - action: couple the schema to one storage provider
        reason: policy shape and persistence are separate decisions
        instead: keep the schema provider-neutral
      do_not_touch:
      - tests/fixtures/toolkit/blueprint.md
      rollback: Remove the additive schema and its focused tests.
      observability: policy schema test pass count
      execution_recipe: diagnose-repair-verify
---
# Policy contract

Separates accepted policy shape from resolution and enforcement.

## Responsibility

Own the completion artifact

## Independent proof

Read the artifact and independently check its exact bytes.

## Rejected alternatives

- **Treat the API handler as the policy boundary** — Handler ownership would mix contract, resolution, and enforcement concerns.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
