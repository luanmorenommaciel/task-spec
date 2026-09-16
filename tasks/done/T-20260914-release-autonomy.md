---
id: T-20260914-release-autonomy
title: "Execute bounded recipes through the attested TaskMesh sandbox"
status: done
format_version: 3
profile: standard
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260914-release-organization]
supersedes: (none)
touches_paths: [mesh, release/mesh, spec/schemas, tests, docs, skills]
creates_paths: []
source_note: "User-authorized release goal and prospective repository-issue pilot, 2026-09-14"
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
execution_backend: codex
signed_off: true
signed_off_by: luanmorenomaciel
signed_off_at: 2026-09-14T20:08:20Z
accepted: true
accepted_by: codex-release-supervisor
accepted_at: 2026-09-16T02:46:09Z
signed_off_sig: hmac-sha256-v3:e2e418a3:71a459926a2760b71fc2af3964543d00a6adfe7c1a368b6f639a90d4997acebd
accepted_tier: 1
accepted_attempt_id: a02c08ce-0abc-4233-8441-a2ec32baadd1
accepted_authorization_ref: hmac-sha256-v3:e2e418a3:71a459926a2760b71fc2af3964543d00a6adfe7c1a368b6f639a90d4997acebd
acceptance_record_digest: sha256:9bc2154f62a8b8525031065f5aa9f8abdf3f22f0ce062c2742f7662a39c06add
---

# Execute bounded recipes through the attested TaskMesh sandbox

> **Why:** Complete the full native toolkit release with verifiable evidence and an organized repository.

## Goal

Execute bounded recipes through the attested TaskMesh sandbox. Preserve established authorization and frozen historical evidence.

## Context

The user explicitly authorized committing and pushing main, creating a release tag and artifact, publishing the release, completing pending capabilities, and running a prospective pilot on real repository issues. Retain historical release evidence and local WATCHDOG.yml bytes.

## Behavior

- **B-1** — GIVEN the approved toolkit and release objective WHEN the scoped release package is completed THEN the package delivers its stated result with direct verification and no unsupported qualification claims

## Success Criteria

```bash
# eval_1: Execute bounded recipes through the attested TaskMesh sandbox
eval_1() {
  go test ./mesh/... && TASKSPEC_REQUIRE_MESH_ISOLATION=1 bash tests/test-mesh-isolation.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "Execute bounded recipes through the attested TaskMesh sandbox"
    runnable: bash
    check_type: deterministic
    verifies: [B-1]
    terminal: true
    expected_duration_sec: 900
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

- Do not weaken or edit the eval contract after sign-off.

## Do-Not-Touch

- `WATCHDOG.yml`
- `release/3.9.0`
- `release/3.8.1`
- `release/3.7`

## Open Questions

(none — this task is fully specified)
