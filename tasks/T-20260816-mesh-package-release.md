---
id: T-20260816-mesh-package-release
title: "Package, document, prove, and privately publish Task-Spec 3.9.0"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260816-mesh-cockpit-mcp]
supersedes: (none)
touches_paths: [VERSION, src/lib/_lib.sh, CHANGELOG.md, package.json, install.sh, Makefile, README.md, SKILL.md, integrations/claude-code/SKILL.md, integrations/claude-code/plugin.json, integrations/claude-code/marketplace.json, .claude-plugin/plugin.json, .claude-plugin/marketplace.json, cmd/taskspec-meshd/main.go, docs, docs/readme-command-coverage.json, .github/workflows, release/evidence.json, release/quality-rubric.json, tools/build-release-archive.py, tools/build-release-report.py, tests/test-release-packaging.sh, tests/test-v36-experience.sh, tests/test-v381-experience.sh, tasks/.plans/task-spec-3.9.0.yaml]
creates_paths: [docs/getting-started/taskmesh.md, docs/reference/taskmesh-contracts.md, docs/trust/taskmesh-boundaries.md, release/3.9.0, tools/build-mesh-release.py, tests/test-mesh-install.sh, tests/test-mesh-conformance.sh, tests/test-mesh-demo.sh]
source_note: "user-approved TaskMesh 3.9.0 release plan"
created: "2026-08-16T00:00:00Z"
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
signed_off: false
signed_off_by: (none)
signed_off_at: (none)
accepted: false
accepted_by: (none)
accepted_at: (none)
---

# Package, document, prove, and privately publish Task-Spec 3.9.0

> **Why:** The optional runtime must be installable and reviewable without regressing the evidence-backed core or overstating external proof.

## Goal

Ship checksummed private mesh binaries for supported platforms, --with-mesh installation, complete docs, demonstrations, retained gates, and a private v3.9.0 release only when all evidence passes.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN a core-only or mesh-enabled installation WHEN its documented journey runs THEN both installation modes pass and helper mismatches fail closed
- **B-2** — GIVEN the v3.9.0 release audit WHEN all local, hosted, isolation, recovery, adapter, cockpit, packaging, and documentation gates run THEN required evidence tokens are backed by executed artifacts and the 3.8.1 score remains at least 97
- **B-3** — GIVEN incomplete external or autonomous evidence WHEN publication is considered THEN the RC remains private and no unsupported claim or final tag is emitted

## Success Criteria

```bash
# eval_1: full core and mesh release corridor passes with retained private evidence
eval_1() {
  make check && bash tests/test-mesh-conformance.sh && bash tests/test-mesh-demo.sh && bash tests/test-mesh-install.sh
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "full core and mesh release corridor passes with retained private evidence"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2, B-3]
    terminal: true
    expected_duration_sec: 600
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

- Do not publish a final tag, pull an image automatically, or claim production reliability from fixtures.

## Do-Not-Touch

- `fixtures/diamond-6`

## Open Questions

(none — this task is fully specified)
