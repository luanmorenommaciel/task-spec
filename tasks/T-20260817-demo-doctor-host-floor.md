---
id: T-20260817-demo-doctor-host-floor
title: "Fail loudly when the demo host floor is missing"
status: sealed
format_version: 3
profile: small
effort: S
budget_iterations: 3
agent: wright
parent: (none)
depends_on: []
supersedes: (none)
children: []
touches_paths:
  - bin/taskspec
  - src/setup/demo.sh
  - src/dispatch/agent-context.py
  - tests/test-demo.sh
creates_paths:
  - tasks/T-20260817-demo-doctor-host-floor.md
source_note: "Assay v3.9.0 live prove: demo exit 1 empty output without shellcheck. Luan go-ahead 2026-08-17 16:01 BRT."
created: "2026-08-17T18:56:00Z"
owner: luan-moreno
priority: P1
severity: defect
signed_off: true
signed_off_by: luan-moreno
signed_off_at: "2026-08-17T19:01:00Z"
accepted: false
accepted_by: (none)
accepted_at: (none)
---

# Fail loudly when the demo host floor is missing

## Goal
A stock host without shellcheck must not get a silent `taskspec demo` fail. Doctor must name the floor.

## Behavior
- B-1 — GIVEN shellcheck is not on PATH WHEN `taskspec demo` THEN stdout has `DEMO=BLOCKED`, the blocker, and a next action; exit is nonzero; stdout/stderr are not both empty.
- B-2 — GIVEN the same host WHEN `taskspec --json demo` THEN the JSON envelope carries that same text (not empty strings).
- B-3 — GIVEN the same host WHEN `taskspec doctor` THEN missing shellcheck is FAIL, the process prints `DOCTOR=BLOCKED` or `DOCTOR=READY`, and `NEXT:`.
- B-4 — GIVEN shellcheck and a signing key WHEN `taskspec demo` THEN the isolated happy path still ends `DEMO=READY`.

## Success Criteria
eval_1: bash tests/test-demo.sh  (happy path + hidden-shellcheck loud fail)

PRE-gate unchanged. No mesh work in this spec.
