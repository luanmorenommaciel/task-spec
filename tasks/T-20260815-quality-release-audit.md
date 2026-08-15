---
id: T-20260815-quality-release-audit
title: "Generate the evidence-backed quality score and release audit"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260815-release-evidence-contracts]
supersedes: (none)
touches_paths: [Makefile, release/evidence.json, README.md]
creates_paths: [release/quality-rubric.json, release/3.8.1/scorecard.json, src/evidence/release_audit.py, tests/test-release-audit.sh]
source_note: "user-approved release train"
created: "2026-08-15T00:00:00Z"
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
execution_backend: codex
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-08-15T17:57:18Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:61a300e7f9b2a2b4359f85a6ace7096a9468924ebd2318c2d77e885d47ad9248
---

# Generate the evidence-backed quality score and release audit

> **Why:** The 97-point claim must be calculated from retained evidence and fail closed on missing proof.

## Goal

Implement QualityRubric/v1, scorecard generation, generated README status, and make release-audit.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN retained evidence with matching digests WHEN the release audit runs THEN the score is derived from fixed criteria without trusting a manually entered total
- **B-2** — GIVEN missing, pending, unavailable, tampered, or mismatched evidence WHEN the audit runs THEN the affected points are denied and the blocking gate fails

## Success Criteria

```bash
# eval_1: score derivation and evidence falsifiers pass
eval_1() {
  bash tests/test-release-audit.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "score derivation and evidence falsifiers pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
    terminal: true
    expected_duration_sec: 45
retry_policy:
  max_iterations: 15
  circuit_breaker_no_progress: 3
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, behavior, contract, guardrails]
  produce: [code, tests]
  required_tools: [git, bash]
  timeout_minutes: 30
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit: [pass, fail, retry_with_reason, parked_with_context]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1
```

## Rollback Plan

Revert only the declared write surface and park the task with context.

## Observability Hooks

(none — no runtime observability required)

## Anti-Patterns

- Do not turn a local pass, contract declaration, or synthetic fixture into external proof.

## Do-Not-Touch

- `release/3.8.1/external`

## Open Questions

(none — this task is fully specified)
