---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-OVERVIEW-SKILL
seam_id: SEAM-OVERVIEW-SKILL
swimlane_id: LANE-OVERVIEW-SKILL
observable_state: Route a new-user orientation request to taskspec guide overview, after inspecting current
  CLI state. Preserve exact root and mirror parity and installed relative links.
proof: The declared evaluator succeeds without widening the write surface.
requires:
- overview-route verified behavior
produces:
- overview-skill verified behavior
tasks:
- id: T-20260914-pilot-overview-skill
  title: Route a new-user orientation request to taskspec guide overview, after inspecting current CLI
    state
  goal: Route a new-user orientation request to taskspec guide overview, after inspecting current CLI
    state. Preserve exact root and mirror parity and installed relative links.
  done_condition: Route a new-user orientation request to taskspec guide overview, after inspecting current
    CLI state. Preserve exact root and mirror parity and installed relative links.
  effort: S
  profile: standard
  execution_backend: claude
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
source_seam_sha256: 3ea357876546d6fb72c97407580ecd73af7b4d103baa758819784f271ff1ca5e
---
# Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

## Observable proof

The declared evaluator succeeds without widening the write surface.

## Runnable leaves

- `T-20260914-pilot-overview-skill` — Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state: Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
