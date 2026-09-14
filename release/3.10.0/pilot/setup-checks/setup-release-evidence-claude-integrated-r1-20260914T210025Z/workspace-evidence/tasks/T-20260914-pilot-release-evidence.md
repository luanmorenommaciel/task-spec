---
id: T-20260914-pilot-release-evidence
title: "Exclude WATCHDOG"
status: ready
format_version: 3
profile: standard
effort: M
budget_iterations: 15
agent: any
parent: (none)
depends_on: []
supersedes: (none)
provenance: {"contract": "TaskPlanProvenance/v1", "initiative": "pilot", "projection_digest": "faa1aa10bb5416e8fd3227a2409f716178671023ca61ac1fe5848dbb15e5a28d", "snapshot": "tasks/.plans/pilot/snapshots/f3628f1a50c28a04f603cf019b12bd4fb598c938d13c11d18231b8c24793c27f.json", "snapshot_digest": "f3628f1a50c28a04f603cf019b12bd4fb598c938d13c11d18231b8c24793c27f"}
proves_capabilities: ["LEG-RELEASE-EVIDENCE"]
touches_paths: [tools/build-release-archive.py]
creates_paths: [docs/examples/pilot-release-evidence.json, docs/examples/pilot-artifacts]
source_note: "tasks/.plans/pilot/legs/LEG-RELEASE-EVIDENCE.md#T-20260914-pilot-release-evidence"
created: "2026-09-14T00:00:00Z"
tags: []
owner: (none)
priority: P2
severity: feature
due_date: (none)
precondition: (none)
blocked_reason: (none)
security_class: (none)
source_action_item: (none)
tracker_ref: (none)
execution_backend: claude
signed_off: true
signed_off_by: pilot-controller
signed_off_at: 2026-09-14T21:00:38Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:5afec2c1:5631fa177decd8dc79b0516ed1793dbb157261e47b42e70a3756a07ad6f77787
---

# Exclude WATCHDOG

> **Why:** Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.

## Goal

Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.

## Context

Intent DI-PILOT-RELEASE-EVIDENCE; seam SEAM-RELEASE-EVIDENCE; swimlane LANE-RELEASE-EVIDENCE; capability leg LEG-RELEASE-EVIDENCE. Done condition: Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.

Applicable intent, capability, and evidence: {"decisions": [{"id": "ADR-PILOT-SCOPE", "owner": "pilot-supervisor", "rationale": "The user authorized real repository issues with prospective intervention recording. This fixed corpus defines the evaluated scope before execution; it does not claim a new human review occurred during each run.", "status": "accepted"}], "evidence": [{"claim": "current", "confidence": 1.0, "id": "E-PILOT-ISSUE", "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "ac848dca90458bdca62cedd9413ba4f7d9ef7ba571a0fba4be7ccf0ec2f4ee0d", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "summary": "A repository issue inspected before comparative execution; source digests and reproduction are retained."}], "intent": {"claim": "proposed", "id": "DI-PILOT-RELEASE-EVIDENCE", "out_of_scope": ["Changes outside the registered write surface.", "Production deployment, policy changes, self-authorization, and independent agents."], "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "ac848dca90458bdca62cedd9413ba4f7d9ef7ba571a0fba4be7ccf0ec2f4ee0d", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "success": ["Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health."], "summary": "Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.", "title": "Archive selection depends on ignore state to exclude local advisor settings"}, "lane": {"id": "LANE-RELEASE-EVIDENCE", "name": "release-evidence delivery", "owner": "pilot-release-evidence"}, "leg": {"id": "LEG-RELEASE-EVIDENCE", "observable_state": "Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.", "produces": ["release-evidence verified behavior"], "proof": "The declared evaluator succeeds without widening the write surface.", "requires": []}, "original_intake": null, "seam": {"consumes": ["registered issue"], "decision_ids": ["ADR-PILOT-SCOPE"], "description": "Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.", "evidence": ["E-PILOT-ISSUE"], "id": "SEAM-RELEASE-EVIDENCE", "independent_proof": "Run the registered independent release-evidence evaluator.", "name": "release-evidence", "owner": "pilot-release-evidence", "produces": ["release-evidence verified behavior"], "rejected_alternatives": [{"alternative": "Merge this responsibility into an unrelated task", "reason": "Its write surface and independently assessable outcome belong to this boundary."}], "responsibility": "Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health."}}

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for release-evidence
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py release-evidence --root .
}

# eval_2: Declared write surface only
eval_2() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py write-boundary --root .
}

# eval_3: Registered issue evidence is unchanged
eval_3() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py source-integrity --root .
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Independent behavioral proof for release-evidence"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: false
    expected_duration_sec: 10
  - id: eval_2
    description: "Declared write surface only"
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: false
    expected_duration_sec: 10
  - id: eval_3
    description: "Registered issue evidence is unchanged"
    runnable: bash
    check_type: deterministic
    verifies: [B-2]
    terminal: true
    expected_duration_sec: 10
retry_policy:
  max_iterations: 15
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  execution_recipe: {"artifacts": ["scoped changes", "evaluation evidence", "concise result"], "context": ["TaskHandoff", "authorized Task-Spec", "declared source evidence"], "contract": "TaskExecutionRecipe/v1", "eval_ids": ["eval_1", "eval_2", "eval_3"], "max_rounds": 3, "no_progress_rounds": 2, "on_failure": "park_with_context", "required_capabilities": ["managed_recipe_v1", "persistent_round_budget", "signed_timeout"], "runner": "taskmesh", "steps": ["Reproduce the failure and gather evidence before choosing a cause.", "Repair the evidenced cause within scope.", "Verify the reproduction and affected regression checks."], "stop_on": ["scope_violation", "authority_changed", "environment_unverified", "budget_exhausted", "cancelled"], "strategy": "diagnose-repair-verify", "strategy_version": "1.0.0"}
  read: [intent, behavior, contract, guardrails]
  produce: [code, tests]
  required_tools: [git, bash, python3]
  timeout_minutes: 10
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1 && eval_2 && eval_3
```

## Rollback Plan

Revert only this isolated candidate change.

## Observability Hooks

Retained provider output, evaluation result, and prospective event journal.

## Anti-Patterns

- Do not weaken the independent evaluator: it would invalidate the comparison; instead fix the behavior within the declared surface.
- Do not expand the scope: it breaks matched permissions; instead report the missing work as a blocker.
- Do not claim success without evidence: a plausible patch does not establish behavior; instead run the independent proof and report failures.

## Do-Not-Touch

- `tests/fixtures/toolkit/pilot-issue.json`
- `tasks`

## Open Questions

(none — this task is fully specified)
