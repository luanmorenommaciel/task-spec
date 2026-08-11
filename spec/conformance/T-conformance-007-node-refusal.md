---
id: T-20260811-conformance-007-node-refusal
title: Conformance — executor refuses XL and XXL composition nodes (C17)
status: ready
format_version: 3
profile: lite
effort: XL
budget_iterations: 1
agent: any
parent: (none)
depends_on: []
children: [T-20260811-conformance-child-one, T-20260811-conformance-child-two]
touches_paths: []
creates_paths: []
source_note: Task-Spec 3.5 format conformance fixture for node composition
created: 2026-08-11T00:00:00Z
tags: [conformance, contract, c17]
execution_backend: any
signed_off: false
signed_off_by: (none)
signed_off_at: (none)
accepted: false
accepted_by: (none)
accepted_at: (none)
---

# Conformance — executor refuses XL and XXL composition nodes (C17)

> **Why:** Composition nodes organize child Task-Specs but are not executable
> leaves. A conformant consumer must refuse direct node dispatch.

## Goal

Demonstrate that an executor recognizes the XL node and records a refusal rather
than attempting repository work.

## Success Criteria

```bash
eval_1() {
  grep -qx 'node_refused effort=XL' spec/conformance/_workdir/c007.log
}
```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: executor records direct composition-node refusal
    runnable: bash
    check_type: deterministic
    terminal: true
    expected_duration_sec: 1
retry_policy:
  max_iterations: 1
  circuit_breaker_no_progress: 1
  on_terminal_failure: park_with_context
agent_contract:
  version: 2
  read: [intent, contract]
  produce: [refusal]
  required_tools: [bash]
  timeout_minutes: 1
  sandbox_type: host
  output_artifacts:
    - path: spec/conformance/_workdir/c007.log
      type: log
  mcp_dependencies: []
  emit: [fail]
  backend_metadata: {}
```

## Exit Check

```bash
eval_1
```
