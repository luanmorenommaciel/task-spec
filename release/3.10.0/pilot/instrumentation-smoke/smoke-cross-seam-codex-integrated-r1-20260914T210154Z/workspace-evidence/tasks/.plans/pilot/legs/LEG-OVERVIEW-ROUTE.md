---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-OVERVIEW-ROUTE
seam_id: SEAM-OVERVIEW-ROUTE
swimlane_id: LANE-OVERVIEW-ROUTE
observable_state: Expose guide overview in human and JSON modes using the installed toolkit index, preserving
  existing guide routes.
proof: The declared evaluator succeeds without widening the write surface.
requires: []
produces:
- overview-route verified behavior
tasks:
- id: T-20260914-pilot-overview-route
  title: Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing
    guide routes
  goal: Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing
    guide routes.
  done_condition: Expose guide overview in human and JSON modes using the installed toolkit index, preserving
    existing guide routes.
  effort: S
  profile: standard
  execution_backend: any
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
source_seam_sha256: 244f4144a3b56619fd7401a8248cbe705f237971e76ccb81c40a5f91dc94cfed
---
# Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.

## Observable proof

The declared evaluator succeeds without widening the write surface.

## Runnable leaves

- `T-20260914-pilot-overview-route` — Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes: Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
