---
schema_version: 1
kind: seam
claim: derived
id: SEAM-INVESTIGATION
name: investigation
description: Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments,
  the exact trust boundary, unsupported required environments, and claims not established by Docker smoke
  evidence. Cite verified source symbols and state remaining uncertainty.
evidence:
- E-PILOT-ISSUE
responsibility: Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments,
  the exact trust boundary, unsupported required environments, and claims not established by Docker smoke
  evidence. Cite verified source symbols and state remaining uncertainty.
consumes:
- registered issue
produces:
- investigation verified behavior
owner: pilot-investigation
independent_proof: Run the registered independent investigation evaluator.
decision_ids:
- ADR-PILOT-SCOPE
rejected_alternatives:
- alternative: Merge this responsibility into an unrelated task
  reason: Its write surface and independently assessable outcome belong to this boundary.
swimlane:
  id: LANE-INVESTIGATION
  name: investigation delivery
  owner: pilot-investigation
  legs:
  - id: LEG-INVESTIGATION
    observable_state: Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance
      environments, the exact trust boundary, unsupported required environments, and claims not established
      by Docker smoke evidence. Cite verified source symbols and state remaining uncertainty.
    proof: The declared evaluator succeeds without widening the write surface.
    requires: []
    produces:
    - investigation verified behavior
    tasks:
    - id: T-20260914-pilot-investigation
      title: Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments,
        the exact trust boundary, unsupported required environments, and claims not established by Docker
        smoke evidence
      goal: Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments,
        the exact trust boundary, unsupported required environments, and claims not established by Docker
        smoke evidence. Cite verified source symbols and state remaining uncertainty.
      done_condition: Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance
        environments, the exact trust boundary, unsupported required environments, and claims not established
        by Docker smoke evidence. Cite verified source symbols and state remaining uncertainty.
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
      - docs/maintainers/recipe-assurance-investigation.md
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
        description: Independent behavioral proof for investigation
        bash: /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py
          investigation --root .
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
      execution_recipe: research-synthesize-verify
      proves_capabilities:
      - LEG-INVESTIGATION
---
# investigation

Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments, the exact trust boundary, unsupported required environments, and claims not established by Docker smoke evidence. Cite verified source symbols and state remaining uncertainty.

## Responsibility

Produce an evidence-grounded maintainer note showing executor/evaluator/acceptance environments, the exact trust boundary, unsupported required environments, and claims not established by Docker smoke evidence. Cite verified source symbols and state remaining uncertainty.

## Independent proof

Run the registered independent investigation evaluator.

## Rejected alternatives

- **Merge this responsibility into an unrelated task** — Its write surface and independently assessable outcome belong to this boundary.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
