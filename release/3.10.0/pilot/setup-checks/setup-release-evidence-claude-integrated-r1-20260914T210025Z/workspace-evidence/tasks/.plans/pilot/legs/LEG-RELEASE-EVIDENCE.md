---
schema_version: 1
kind: capability-leg
claim: derived
id: LEG-RELEASE-EVIDENCE
seam_id: SEAM-RELEASE-EVIDENCE
swimlane_id: LANE-RELEASE-EVIDENCE
observable_state: Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance
  state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and
  record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json
  as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not
  claim deployment health.
proof: The declared evaluator succeeds without widening the write surface.
requires: []
produces:
- release-evidence verified behavior
tasks:
- id: T-20260914-pilot-release-evidence
  title: Exclude WATCHDOG
  goal: Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state.
    Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record
    the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as
    reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim
    deployment health.
  done_condition: Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance
    state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum,
    and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json
    as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not
    claim deployment health.
  effort: M
  profile: standard
  execution_backend: claude
  required_tools:
  - git
  - bash
  - python3
  depends_on: []
  touches_paths:
  - tools/build-release-archive.py
  creates_paths:
  - docs/examples/pilot-release-evidence.json
  - docs/examples/pilot-artifacts
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
    description: Independent behavioral proof for release-evidence
    bash: /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py
      release-evidence --root .
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
  - LEG-RELEASE-EVIDENCE
source_seam_sha256: 3aebc56dd4c9bdcdee1fbbf952e8d6ced8058feb3f563c25e1adaf2db5702ee6
---
# Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.

## Observable proof

The declared evaluator succeeds without widening the write surface.

## Runnable leaves

- `T-20260914-pilot-release-evidence` — Exclude WATCHDOG: Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.

The leg names a capability state, not an activity. Each leaf owns one coherent,
independently provable done-condition.
