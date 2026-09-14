---
schema_version: 1
kind: seam
claim: derived
id: SEAM-OVERVIEW-ROUTE
name: overview-route
description: Expose guide overview in human and JSON modes using the installed toolkit index, preserving
  existing guide routes.
evidence:
- E-PILOT-ISSUE
responsibility: Expose guide overview in human and JSON modes using the installed toolkit index, preserving
  existing guide routes.
consumes:
- registered issue
produces:
- overview-route verified behavior
owner: pilot-overview-route
independent_proof: Run the registered independent overview-route evaluator.
decision_ids:
- ADR-PILOT-SCOPE
rejected_alternatives:
- alternative: Merge this responsibility into an unrelated task
  reason: Its write surface and independently assessable outcome belong to this boundary.
swimlane:
  id: LANE-OVERVIEW-ROUTE
  name: overview-route delivery
  owner: pilot-overview-route
  legs:
  - id: LEG-OVERVIEW-ROUTE
    observable_state: Expose guide overview in human and JSON modes using the installed toolkit index,
      preserving existing guide routes.
    proof: The declared evaluator succeeds without widening the write surface.
    requires: []
    produces:
    - overview-route verified behavior
    tasks:
    - id: T-20260914-pilot-overview-route
      title: Expose guide overview in human and JSON modes using the installed toolkit index, preserving
        existing guide routes
      goal: Expose guide overview in human and JSON modes using the installed toolkit index, preserving
        existing guide routes.
      done_condition: Expose guide overview in human and JSON modes using the installed toolkit index,
        preserving existing guide routes.
      effort: S
      profile: standard
      execution_backend: claude
      required_tools:
      - git
      - bash
      - python3
      depends_on: []
      touches_paths:
      - src/cli/guide.py
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
        description: Independent behavioral proof for overview-route
        bash: /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py
          overview-route --root .
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
---
# overview-route

Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.

## Responsibility

Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.

## Independent proof

Run the registered independent overview-route evaluator.

## Rejected alternatives

- **Merge this responsibility into an unrelated task** — Its write surface and independently assessable outcome belong to this boundary.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
