---
id: T-20260914-pilot-overview-route
title: "Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes"
status: done
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: []
supersedes: (none)
provenance: {"contract": "TaskPlanProvenance/v1", "initiative": "pilot", "projection_digest": "9a00d37151b30a6dba205512d102b8964c809ce6a23d2f088d171bb896432d61", "snapshot": "tasks/.plans/pilot/snapshots/67a67aa69120c57f9d0cac85704f1f814577d60128091a796dd3ba2c0dc454c0.json", "snapshot_digest": "67a67aa69120c57f9d0cac85704f1f814577d60128091a796dd3ba2c0dc454c0"}
touches_paths: [src/cli/guide.py]
creates_paths: []
source_note: "tasks/.plans/pilot/legs/LEG-OVERVIEW-ROUTE.md#T-20260914-pilot-overview-route"
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
execution_backend: any
signed_off: true
signed_off_by: pilot-controller
signed_off_at: 2026-09-14T21:02:13Z
accepted: true
accepted_by: luanmorenomaciel
accepted_at: 2026-09-14T21:02:49Z
signed_off_sig: hmac-sha256-v3:afd77c01:2f0af49998a16d6d7582df042f080aadceab71c3d914150a7be6e608df100ba0
accepted_tier: 1
accepted_attempt_id: 9f07339c-742a-4955-a519-866a33822bd8
accepted_authorization_ref: hmac-sha256-v3:afd77c01:2f0af49998a16d6d7582df042f080aadceab71c3d914150a7be6e608df100ba0
acceptance_record_digest: sha256:46f9ddcec4660aafdcf150a33ad0d998ef51cea8a1578a9746a138298549978a
---

# Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes

> **Why:** Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.

## Goal

Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.

## Context

Intent DI-PILOT-CROSS-SEAM; seam SEAM-OVERVIEW-ROUTE; swimlane LANE-OVERVIEW-ROUTE; capability leg LEG-OVERVIEW-ROUTE. Done condition: Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.

Applicable intent, capability, and evidence: {"decisions": [{"id": "ADR-PILOT-SCOPE", "owner": "pilot-supervisor", "rationale": "The user authorized real repository issues with prospective intervention recording. This fixed corpus defines the evaluated scope before execution; it does not claim a new human review occurred during each run.", "status": "accepted"}], "evidence": [{"claim": "current", "confidence": 1.0, "id": "E-PILOT-ISSUE", "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "9cb2693bd26a714755d6a8800e2870c5a639be060372c6cb2dc0bbdde349b570", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "summary": "A repository issue inspected before comparative execution; source digests and reproduction are retained."}], "intent": {"claim": "proposed", "id": "DI-PILOT-CROSS-SEAM", "out_of_scope": ["Changes outside the registered write surface.", "Production deployment, policy changes, self-authorization, and independent agents."], "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "9cb2693bd26a714755d6a8800e2870c5a639be060372c6cb2dc0bbdde349b570", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "success": ["Expose guide overview in human and JSON modes and route a new-user skill request to the installed overview, preserving root/mirror parity and links."], "summary": "Expose guide overview in human and JSON modes and route a new-user skill request to the installed overview, preserving root/mirror parity and links.", "title": "The installed toolkit overview has no CLI route or skill entry"}, "lane": {"id": "LANE-OVERVIEW-ROUTE", "name": "overview-route delivery", "owner": "pilot-overview-route"}, "leg": {"id": "LEG-OVERVIEW-ROUTE", "observable_state": "Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.", "produces": ["overview-route verified behavior"], "proof": "The declared evaluator succeeds without widening the write surface.", "requires": []}, "original_intake": null, "seam": {"consumes": ["registered issue"], "decision_ids": ["ADR-PILOT-SCOPE"], "description": "Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes.", "evidence": ["E-PILOT-ISSUE"], "id": "SEAM-OVERVIEW-ROUTE", "independent_proof": "Run the registered independent overview-route evaluator.", "name": "overview-route", "owner": "pilot-overview-route", "produces": ["overview-route verified behavior"], "rejected_alternatives": [{"alternative": "Merge this responsibility into an unrelated task", "reason": "Its write surface and independently assessable outcome belong to this boundary."}], "responsibility": "Expose guide overview in human and JSON modes using the installed toolkit index, preserving existing guide routes."}}

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for overview-route
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py overview-route --root .
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
    description: "Independent behavioral proof for overview-route"
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
