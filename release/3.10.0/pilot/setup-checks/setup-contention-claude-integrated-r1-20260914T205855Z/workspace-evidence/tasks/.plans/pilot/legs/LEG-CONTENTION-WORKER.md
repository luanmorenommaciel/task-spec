---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-CONTENTION-WORKER
seam_id: SEAM-CONTENTION-WORKER
swimlane_id: LANE-CONTENTION-WORKER
observable_state: 'Provide a local test worker: --version prints resource-worker/1; normal invocation
  remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact
  providers.'
proof: The declared evaluator succeeds without widening the write surface.
requires: []
produces:
- contention-worker verified behavior
tasks:
- id: T-20260914-pilot-contention-worker
  title: 'Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive
    until cancellation and exits cleanly on TERM'
  goal: 'Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive
    until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.'
  done_condition: 'Provide a local test worker: --version prints resource-worker/1; normal invocation
    remains alive until cancellation and exits cleanly on TERM. It must not change repository files or
    contact providers.'
  effort: S
  profile: standard
  execution_backend: claude
  required_tools:
  - git
  - bash
  - python3
  depends_on: []
  touches_paths: []
  creates_paths:
  - tests/fixtures/toolkit/resource-worker.sh
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
    description: Independent behavioral proof for contention-worker
    bash: /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py
      contention-worker --root .
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
source_seam_sha256: f91d0d75d663e602b70ec6dc6234b37bc6ba4ac3b46707c752db875355b6b914
---
# Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

## Observable proof

The declared evaluator succeeds without widening the write surface.

## Runnable leaves

- `T-20260914-pilot-contention-worker` — Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM: Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
