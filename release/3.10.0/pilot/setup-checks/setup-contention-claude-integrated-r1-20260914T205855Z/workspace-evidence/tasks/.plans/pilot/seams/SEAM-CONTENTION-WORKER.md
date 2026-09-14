---
schema_version: 1
kind: seam
claim: derived
id: SEAM-CONTENTION-WORKER
name: contention-worker
description: 'Provide a local test worker: --version prints resource-worker/1; normal invocation remains
  alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.'
evidence:
- E-PILOT-ISSUE
responsibility: 'Provide a local test worker: --version prints resource-worker/1; normal invocation remains
  alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.'
consumes:
- registered issue
produces:
- contention-worker verified behavior
owner: pilot-contention-worker
independent_proof: Run the registered independent contention-worker evaluator.
decision_ids:
- ADR-PILOT-SCOPE
rejected_alternatives:
- alternative: Merge this responsibility into an unrelated task
  reason: Its write surface and independently assessable outcome belong to this boundary.
swimlane:
  id: LANE-CONTENTION-WORKER
  name: contention-worker delivery
  owner: pilot-contention-worker
  legs:
  - id: LEG-CONTENTION-WORKER
    observable_state: 'Provide a local test worker: --version prints resource-worker/1; normal invocation
      remains alive until cancellation and exits cleanly on TERM. It must not change repository files
      or contact providers.'
    proof: The declared evaluator succeeds without widening the write surface.
    requires: []
    produces:
    - contention-worker verified behavior
    tasks:
    - id: T-20260914-pilot-contention-worker
      title: 'Provide a local test worker: --version prints resource-worker/1; normal invocation remains
        alive until cancellation and exits cleanly on TERM'
      goal: 'Provide a local test worker: --version prints resource-worker/1; normal invocation remains
        alive until cancellation and exits cleanly on TERM. It must not change repository files or contact
        providers.'
      done_condition: 'Provide a local test worker: --version prints resource-worker/1; normal invocation
        remains alive until cancellation and exits cleanly on TERM. It must not change repository files
        or contact providers.'
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
---
# contention-worker

Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

## Responsibility

Provide a local test worker: --version prints resource-worker/1; normal invocation remains alive until cancellation and exits cleanly on TERM. It must not change repository files or contact providers.

## Independent proof

Run the registered independent contention-worker evaluator.

## Rejected alternatives

- **Merge this responsibility into an unrelated task** — Its write surface and independently assessable outcome belong to this boundary.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
