---
schema_version: 1
kind: seam
claim: derived
id: SEAM-OVERVIEW-SKILL
name: overview-skill
description: Route a new-user orientation request to taskspec guide overview, after inspecting current
  CLI state. Preserve exact root and mirror parity and installed relative links.
evidence:
- E-PILOT-ISSUE
responsibility: Route a new-user orientation request to taskspec guide overview, after inspecting current
  CLI state. Preserve exact root and mirror parity and installed relative links.
consumes:
- overview-route verified behavior
produces:
- overview-skill verified behavior
owner: pilot-overview-skill
independent_proof: Run the registered independent overview-skill evaluator.
decision_ids:
- ADR-PILOT-SCOPE
rejected_alternatives:
- alternative: Merge this responsibility into an unrelated task
  reason: Its write surface and independently assessable outcome belong to this boundary.
swimlane:
  id: LANE-OVERVIEW-SKILL
  name: overview-skill delivery
  owner: pilot-overview-skill
  legs:
  - id: LEG-OVERVIEW-SKILL
    observable_state: Route a new-user orientation request to taskspec guide overview, after inspecting
      current CLI state. Preserve exact root and mirror parity and installed relative links.
    proof: The declared evaluator succeeds without widening the write surface.
    requires:
    - overview-route verified behavior
    produces:
    - overview-skill verified behavior
    tasks:
    - id: T-20260914-pilot-overview-skill
      title: Route a new-user orientation request to taskspec guide overview, after inspecting current
        CLI state
      goal: Route a new-user orientation request to taskspec guide overview, after inspecting current
        CLI state. Preserve exact root and mirror parity and installed relative links.
      done_condition: Route a new-user orientation request to taskspec guide overview, after inspecting
        current CLI state. Preserve exact root and mirror parity and installed relative links.
      effort: S
      profile: standard
      execution_backend: any
      required_tools:
      - git
      - bash
      - python3
      depends_on:
      - T-20260914-pilot-overview-route
      touches_paths:
      - SKILL.md
      - skills/task-spec/SKILL.md
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
        description: Independent behavioral proof for overview-skill
        bash: /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py
          cross-seam --root .
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
      - LEG-OVERVIEW-ROUTE
      - LEG-OVERVIEW-SKILL
---
# overview-skill

Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

## Responsibility

Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

## Independent proof

Run the registered independent overview-skill evaluator.

## Rejected alternatives

- **Merge this responsibility into an unrelated task** — Its write surface and independently assessable outcome belong to this boundary.

This derived seam is ready only while its cited evidence, named owner, contract,
and rejected alternatives remain intact.
