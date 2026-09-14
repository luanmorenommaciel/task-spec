---
schema_version: 1
kind: seam
claim: derived
id: SEAM-CONTENTION
name: contention
description: Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource,
  a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve
  one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held
  attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse,
  and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not
  use an installed helper from another checkout.
evidence:
- E-PILOT-ISSUE
responsibility: Add an isolated end-to-end regression where disjoint file changes claim one exclusive
  resource, a second run refuses the live conflict, and the resource becomes available after cancellation.
  Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh
  for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse,
  and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not
  use an installed helper from another checkout.
consumes:
- contention-worker verified behavior
produces:
- contention verified behavior
owner: pilot-contention
independent_proof: Run the registered independent contention evaluator.
decision_ids:
- ADR-PILOT-SCOPE
rejected_alternatives:
- alternative: Merge this responsibility into an unrelated task
  reason: Its write surface and independently assessable outcome belong to this boundary.
swimlane:
  id: LANE-CONTENTION
  name: contention delivery
  owner: pilot-contention
  legs:
  - id: LEG-CONTENTION
    observable_state: Add an isolated end-to-end regression where disjoint file changes claim one exclusive
      resource, a second run refuses the live conflict, and the resource becomes available after cancellation.
      Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh
      for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal,
      cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository
      with its VERSION; do not use an installed helper from another checkout.
    proof: The declared evaluator succeeds without widening the write surface.
    requires:
    - contention-worker verified behavior
    produces:
    - contention verified behavior
    tasks:
    - id: T-20260914-pilot-contention
      title: Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource,
        a second run refuses the live conflict, and the resource becomes available after cancellation
      goal: Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource,
        a second run refuses the live conflict, and the resource becomes available after cancellation.
        Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh
        for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal,
        cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository
        with its VERSION; do not use an installed helper from another checkout.
      done_condition: Add an isolated end-to-end regression where disjoint file changes claim one exclusive
        resource, a second run refuses the live conflict, and the resource becomes available after cancellation.
        Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh
        for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal,
        cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository
        with its VERSION; do not use an installed helper from another checkout.
      effort: S
      profile: standard
      execution_backend: claude
      required_tools:
      - git
      - bash
      - python3
      depends_on:
      - T-20260914-pilot-contention-worker
      touches_paths: []
      creates_paths:
      - tests/test-toolkit-resource-contention.sh
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
        description: Independent behavioral proof for contention
        bash: /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py
          contention --root .
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
      - LEG-CONTENTION-WORKER
      - LEG-CONTENTION
---
# contention

Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.

## Responsibility

Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state. Use tests/fixtures/toolkit/resource-worker.sh for the held attempt. Print TOOLKIT_RESOURCE_CONTENTION=PASS only after the live resource refusal, cancellation/reuse, and unchanged target assertions pass. Compile the helper from this repository with its VERSION; do not use an installed helper from another checkout.

## Independent proof

Run the registered independent contention evaluator.

## Rejected alternatives

- **Merge this responsibility into an unrelated task** — Its write surface and independently assessable outcome belong to this boundary.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
