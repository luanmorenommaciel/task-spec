---
schema_version: 1
kind: delivery-intent
id: INT-RATE-LIMITING
title: Organization-scoped request rate limiting steel thread
claim: external
source:
  uri: tests/fixtures/toolkit/blueprint.md
  captured_at: '2026-09-15T00:00:00Z'
  sha256: f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445
success:
- A versioned policy schema rejects invalid limits and windows and accepts valid ones.
- Resolution produces exactly one effective policy for an organization, or a typed no-policy result.
- Request 101 is denied after 100 allowed requests in the same window.
- The denial returns a stable machine-readable reason and emits matching decision telemetry.
out_of_scope:
- 'Provider-owned usage metering: it keeps its current provider ownership and is consumed only as an external
  boundary.'
- Selection of production storage and deployment infrastructure.
- Billing, quota reconciliation, or any write into metering records.
---
# Organization-scoped request rate limiting steel thread

## Delivery outcome

Deliver the four-step steel thread stated in the source fixture: a versioned policy schema that rejects invalid limits and windows, resolution to exactly one effective policy per organization, denial of request 101 after 100 allowed requests in the same window, and a stable denial reason with matching decision telemetry.

## Evidence boundary

This artifact records a **external** claim. Its source, capture time,
and content hash are recorded in frontmatter; the claim is not implementation
evidence by itself.
