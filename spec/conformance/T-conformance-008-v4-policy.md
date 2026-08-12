---
id: T-20260812-v4-policy
title: Preserve the format-v4 evidence policy during execution
status: ready
format_version: 4
profile: lite
effort: XS
budget_iterations: 1
agent: any
parent: (none)
depends_on: []
touches_paths: [spec/conformance/_workdir/c008.log]
creates_paths: []
source_note: conformance fixture C18
created: 2026-08-12T12:00:00Z
tags: [conformance, v4]
owner: conformance
priority: P1
severity: feature
execution_backend: any
signed_off: false
signed_off_by: (none)
signed_off_at: (none)
accepted: false
accepted_by: (none)
accepted_at: (none)
evaluation_policy:
  acceptance_scope: local
  deterministic:
    required: true
  holdout:
    required: false
  graded:
    required: false
  human:
    required: false
identity_policy:
  required: false
---

# Preserve the format-v4 evidence policy

> **Why:** An executor must receive the policy but must not silently weaken it.

## Goal

Record that format v4 and its deterministic evidence requirement were observed.

## Success Criteria

```bash
eval_1() {
  grep -qx 'format=4 deterministic=required policy=preserved' spec/conformance/_workdir/c008.log
}
```

## Validation Card

```yaml
success_criteria:
  - id: eval_1
    description: The v4 policy is propagated without weakening
    runnable: bash
    check_type: deterministic
    terminal: true
    expected_duration_sec: 1
retry_policy:
  max_iterations: 1
  circuit_breaker_no_progress: 1
  on_terminal_failure: fail_loudly
agent_contract:
  version: 2
  read: [intent, contract]
  produce: [docs]
  required_tools: [bash]
  timeout_minutes: 1
  sandbox_type: host
  output_artifacts: []
  mcp_dependencies: []
  emit: [pass, fail]
```

## Exit Check

```bash
eval_1
```
