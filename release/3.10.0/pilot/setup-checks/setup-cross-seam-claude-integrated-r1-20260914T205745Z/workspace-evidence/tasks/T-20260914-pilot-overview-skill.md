---
id: T-20260914-pilot-overview-skill
title: "Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state"
status: ready
format_version: 3
profile: standard
effort: S
budget_iterations: 15
agent: any
parent: (none)
depends_on: [T-20260914-pilot-overview-route]
supersedes: (none)
provenance: {"contract": "TaskPlanProvenance/v1", "initiative": "pilot", "projection_digest": "6ebbf40bb8fa15258b83916aae6d5499bf897caf9f8f9da2bdd3946fd4d0a0d9", "snapshot": "tasks/.plans/pilot/snapshots/cdf1ce1fafb79d505a3e888ade146078391429c13edcfba6f010048bd0b508b4.json", "snapshot_digest": "cdf1ce1fafb79d505a3e888ade146078391429c13edcfba6f010048bd0b508b4"}
proves_capabilities: ["LEG-OVERVIEW-ROUTE", "LEG-OVERVIEW-SKILL"]
touches_paths: [SKILL.md, skills/task-spec/SKILL.md]
creates_paths: []
source_note: "tasks/.plans/pilot/legs/LEG-OVERVIEW-SKILL.md#T-20260914-pilot-overview-skill"
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
signed_off_at: 2026-09-14T20:57:59Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:11dd0426:d7ff29203b0d59c893d48d9c7d29d0e793a422cd06438769d304961a3224d071
---

# Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state

> **Why:** Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

## Goal

Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

## Context

Intent DI-PILOT-CROSS-SEAM; seam SEAM-OVERVIEW-SKILL; swimlane LANE-OVERVIEW-SKILL; capability leg LEG-OVERVIEW-SKILL. Done condition: Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.

Applicable intent, capability, and evidence: {"decisions": [{"id": "ADR-PILOT-SCOPE", "owner": "pilot-supervisor", "rationale": "The user authorized real repository issues with prospective intervention recording. This fixed corpus defines the evaluated scope before execution; it does not claim a new human review occurred during each run.", "status": "accepted"}], "evidence": [{"claim": "current", "confidence": 1.0, "id": "E-PILOT-ISSUE", "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "9cb2693bd26a714755d6a8800e2870c5a639be060372c6cb2dc0bbdde349b570", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "summary": "A repository issue inspected before comparative execution; source digests and reproduction are retained."}], "intent": {"claim": "proposed", "id": "DI-PILOT-CROSS-SEAM", "out_of_scope": ["Changes outside the registered write surface.", "Production deployment, policy changes, self-authorization, and independent agents."], "source": {"captured_at": "2026-09-14T20:20:46.550715+00:00", "sha256": "9cb2693bd26a714755d6a8800e2870c5a639be060372c6cb2dc0bbdde349b570", "uri": "tests/fixtures/toolkit/pilot-issue.json"}, "success": ["Expose guide overview in human and JSON modes and route a new-user skill request to the installed overview, preserving root/mirror parity and links."], "summary": "Expose guide overview in human and JSON modes and route a new-user skill request to the installed overview, preserving root/mirror parity and links.", "title": "The installed toolkit overview has no CLI route or skill entry"}, "lane": {"id": "LANE-OVERVIEW-SKILL", "name": "overview-skill delivery", "owner": "pilot-overview-skill"}, "leg": {"id": "LEG-OVERVIEW-SKILL", "observable_state": "Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.", "produces": ["overview-skill verified behavior"], "proof": "The declared evaluator succeeds without widening the write surface.", "requires": ["overview-route verified behavior"]}, "original_intake": null, "seam": {"consumes": ["overview-route verified behavior"], "decision_ids": ["ADR-PILOT-SCOPE"], "description": "Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links.", "evidence": ["E-PILOT-ISSUE"], "id": "SEAM-OVERVIEW-SKILL", "independent_proof": "Run the registered independent overview-skill evaluator.", "name": "overview-skill", "owner": "pilot-overview-skill", "produces": ["overview-skill verified behavior"], "rejected_alternatives": [{"alternative": "Merge this responsibility into an unrelated task", "reason": "Its write surface and independently assessable outcome belong to this boundary."}], "responsibility": "Route a new-user orientation request to taskspec guide overview, after inspecting current CLI state. Preserve exact root and mirror parity and installed relative links."}}

## Behavior

- **B-1** — GIVEN the registered repository issue and fixed authorized scope WHEN the bounded implementation is independently evaluated THEN the declared behavior passes without modifying unrelated files or promoting reported evidence
- **B-2** — GIVEN the recorded evidence and authorization boundary WHEN the candidate is checked THEN source evidence is unchanged and no unrelated write is present

## Success Criteria

```bash
# eval_1: Independent behavioral proof for overview-skill
eval_1() {
  /Users/luanmorenomaciel/GitHub/task-spec/.taskspec/runtime/decompose/bin/python /Users/luanmorenomaciel/GitHub/task-spec/tests/evals/toolkit/evaluate_issue.py cross-seam --root .
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
    description: "Independent behavioral proof for overview-skill"
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
