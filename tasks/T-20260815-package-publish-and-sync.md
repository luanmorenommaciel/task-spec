---
id: T-20260815-package-publish-and-sync
title: "Package, attest, publish, and synchronize Task-Spec 3.8.1"
status: ready
format_version: 3
profile: full
effort: L
budget_iterations: 15
agent: codex
parent: (none)
depends_on: [T-20260815-installed-example-and-docs, T-20260815-real-engine-benchmark, T-20260815-signed-sandbox-attestation]
supersedes: (none)
touches_paths: [VERSION, src/lib/_lib.sh, CHANGELOG.md, package.json, install.sh, README.md, SKILL.md, spec/task-spec-v3.md, spec/task-spec-v4.md, .claude-plugin, integrations/claude-code, .github/workflows, tools/build-release-archive.py, release/evidence.json, release/3.8.1, release/docker, tests/test-v36-experience.sh, tests/fixtures/task-materialization-receipt.json]
creates_paths: [release/3.8.1/checksums.txt, release/3.8.1/release-report.json, release/3.8.1/local-gates.json, release/3.8.1/install-matrix.json, release/3.8.1/sbom.spdx.json, tools/build-sbom.py, tools/build-release-evidence-archive.py, tests/test-release-packaging.sh]
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
signed_off_at: 2026-08-15T19:50:58Z
accepted: false
accepted_by: (none)
accepted_at: (none)
signed_off_sig: hmac-sha256-v3:e2e418a3:5543ea85164c79e2471176c640dc0310abd7f48dd66a3e7e25dba3980b8a90b3
---

# Package, attest, publish, and synchronize Task-Spec 3.8.1

> **Why:** The evidence-backed release must be installable, attestable, hosted, and synchronized without weakening truth boundaries.

## Goal

Produce the final 3.8.1 artifacts, pass hosted and remote gates, publish the tag, and update Converge from the immutable export.

## Context

(none — the manifest contains all execution context)

## Behavior

- **B-1** — GIVEN all blocking evidence is verified WHEN the release is packaged THEN versions, archives, checksums, SBOM, provenance, installers, release evidence, and documentation agree
- **B-2** — GIVEN any blocking evidence is pending, unavailable, not run, failed, or billing-blocked WHEN publication is attempted THEN the final tag is refused

## Success Criteria

```bash
# eval_1: local packaging and publication-preflight gates pass
eval_1() {
  bash tests/test-release-packaging.sh && make release-audit
}

```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: "local packaging and publication-preflight gates pass"
    runnable: bash
    check_type: deterministic
    verifies: [B-1, B-2]
    terminal: true
    expected_duration_sec: 180
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

- Do not tag, publish, or synchronize Converge before every blocking gate is satisfied.

## Do-Not-Touch

- `/Users/luanmorenomaciel/GitHub/converge`

## Open Questions

(none — this task is fully specified)
