---
schema_version: 1
kind: decision
id: DEC-FIXED-WINDOW
status: proposed
owner: pending human assignment at plan review
rationale: The source says request 101 is denied after 100 allowed requests in the same window without
  naming the algorithm. This recipe proposes a fixed window keyed by organization and window start with
  an injected clock, as the minimal reading of the source. A sliding-window requirement would change the
  counter leaf and its evals.
---
# DEC-FIXED-WINDOW

Status: **proposed**

Owner: pending human assignment at plan review

## Rationale

The source says request 101 is denied after 100 allowed requests in the same window without naming the algorithm. This recipe proposes a fixed window keyed by organization and window start with an injected clock, as the minimal reading of the source. A sliding-window requirement would change the counter leaf and its evals.
