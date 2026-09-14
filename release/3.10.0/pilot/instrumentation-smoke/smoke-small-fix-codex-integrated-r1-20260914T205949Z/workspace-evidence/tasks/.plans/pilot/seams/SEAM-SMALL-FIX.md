---
schema_version: 1
kind: seam
claim: derived
id: SEAM-SMALL-FIX
name: small-fix
description: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input;
  preserve file validation.
evidence:
- E-PILOT-ISSUE
responsibility: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file
  input; preserve file validation.
consumes:
- registered issue
produces:
- small-fix verified behavior
owner: pilot-small-fix
independent_proof: Run the registered independent small-fix evaluator.
decision_ids:
- ADR-PILOT-SCOPE
rejected_alternatives:
- alternative: Merge this responsibility into an unrelated task
  reason: Its write surface and independently assessable outcome belong to this boundary.
swimlane:
  id: LANE-SMALL-FIX
  name: small-fix delivery
  owner: pilot-small-fix
  legs:
  - id: LEG-SMALL-FIX
    observable_state: Accept valid stdin JSON and reject malformed stdin with the same typed errors as
      file input; preserve file validation.
    proof: The declared evaluator succeeds without widening the write surface.
    requires: []
    produces:
    - small-fix verified behavior
    tasks:
    - id: T-20260914-pilot-small-fix
      title: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input;
        preserve file validation
      goal: Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input;
        preserve file validation.
      done_condition: Accept valid stdin JSON and reject malformed stdin with the same typed errors as
        file input; preserve file validation.
      effort: S
      profile: standard
      execution_backend: any
      required_tools:
      - git
      - bash
      - python3
      depends_on: []
      touches_paths:
      - src/recipe/recipes.py
      creates_paths: []
      behavior:
      - id: B-1
        given: the registered repository issue and fixed authorized scope
        when: the bounded implementation is independently evaluated
        then: the declared behavior passes without modifying unrelated files or promoting reported evidence
      - id: B-2
        given: the recorded evidence and authorization boundary
        when: the candidate is checked
        then: source evidence is unchanged and no unrelated write is present
      evals:
      - id: eval_1
        description: Independent behavioral proof for small-fix
        bash: /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py
          small-fix --root .
        verifies:
        - B-1
      - id: eval_2
        description: Declared write surface only
        bash: /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py
          write-boundary --root .
        verifies:
        - B-2
      - id: eval_3
        description: Registered issue evidence is unchanged
        bash: /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py
          source-integrity --root .
        verifies:
        - B-2
      anti_patterns:
      - action: weaken the independent evaluator
        reason: it would invalidate the comparison
        instead: fix the behavior within the declared surface
      - action: expand the scope
        reason: it breaks matched permissions
        instead: report the missing work as a blocker
      - action: claim success without evidence
        reason: a plausible patch does not establish behavior
        instead: run the independent proof and report failures
      do_not_touch:
      - tests/fixtures/toolkit/pilot-issue.json
      - tasks
      rollback: Revert only this isolated candidate change.
      observability: Retained provider output, evaluation result, and prospective event journal.
      execution_recipe: diagnose-repair-verify
      proves_capabilities:
      - LEG-SMALL-FIX
---
# small-fix

Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

## Responsibility

Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

## Independent proof

Run the registered independent small-fix evaluator.

## Rejected alternatives

- **Merge this responsibility into an unrelated task** — Its write surface and independently assessable outcome belong to this boundary.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
