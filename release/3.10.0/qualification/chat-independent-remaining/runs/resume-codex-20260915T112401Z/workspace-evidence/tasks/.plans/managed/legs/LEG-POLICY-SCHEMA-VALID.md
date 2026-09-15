---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-POLICY-SCHEMA-VALID
seam_id: SEAM-POLICY-CONTRACT
swimlane_id: LANE-POLICY-CONTRACT
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
source_seam_sha256: 0ffe1f1eb35a855cfa1f183c49a44798e3f4b606a6437a8a7ebde8a4d9e9cee4
---
# The completion artifact contains its accepted value

## Observable proof

Exact output and untouched sibling checks pass.

## Runnable leaves

- `T-20260914-chat-output` — Complete the output artifact: a.txt contains completed and b.txt remains empty.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
