---
schema_version: 1
kind: delivery-intent
id: DI-PILOT-SMALL-FIX
title: Valid execution recipes cannot be piped to recipe validate -
claim: proposed
source:
  uri: tests/fixtures/toolkit/pilot-issue.json
  captured_at: '2026-09-14T20:20:46.550715+00:00'
  sha256: 0644414bcd86c5f0db2533901eb442e352d7feaf0cadf526a7e0dc9d392add23
success:
- Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve
  file validation.
out_of_scope:
- Changes outside the registered write surface.
- Production deployment, policy changes, self-authorization, and independent agents.
---
# Valid execution recipes cannot be piped to recipe validate -

## Delivery outcome

Accept valid stdin JSON and reject malformed stdin with the same typed errors as file input; preserve file validation.

## Evidence boundary

This artifact records a **proposed** claim. Its source, capture time,
and content hash are recorded in frontmatter; the claim is not implementation
evidence by itself.
