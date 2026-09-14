---
schema_version: 1
kind: delivery-intent
id: DI-PILOT-INCIDENT
title: A malformed imported incident receipt raises a raw TypeError
claim: proposed
source:
  uri: tests/fixtures/toolkit/pilot-issue.json
  captured_at: '2026-09-14T20:20:46.550715+00:00'
  sha256: c0183f60ddf3d93d84864cc710e3afd3447caead3920173f91a27a95ce59c610
success:
- Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment
  entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and
  prohibit health or acceptance promotion.
out_of_scope:
- Changes outside the registered write surface.
- Production deployment, policy changes, self-authorization, and independent agents.
---
# A malformed imported incident receipt raises a raw TypeError

## Delivery outcome

Validate imported envelope shape before dereferencing attachments; refuse null/non-list/non-object attachment entries and unexpected envelope keys with OPERATIONAL_INVALID. Preserve valid reported receipts and prohibit health or acceptance promotion.

## Evidence boundary

This artifact records a **proposed** claim. Its source, capture time,
and content hash are recorded in frontmatter; the claim is not implementation
evidence by itself.
