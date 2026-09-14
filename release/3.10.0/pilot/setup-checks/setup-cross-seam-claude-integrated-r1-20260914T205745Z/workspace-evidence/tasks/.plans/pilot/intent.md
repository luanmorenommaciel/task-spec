---
schema_version: 1
kind: delivery-intent
id: DI-PILOT-CROSS-SEAM
title: The installed toolkit overview has no CLI route or skill entry
claim: proposed
source:
  uri: tests/fixtures/toolkit/pilot-issue.json
  captured_at: '2026-09-14T20:20:46.550715+00:00'
  sha256: 9cb2693bd26a714755d6a8800e2870c5a639be060372c6cb2dc0bbdde349b570
success:
- Expose guide overview in human and JSON modes and route a new-user skill request to the installed overview,
  preserving root/mirror parity and links.
out_of_scope:
- Changes outside the registered write surface.
- Production deployment, policy changes, self-authorization, and independent agents.
---
# The installed toolkit overview has no CLI route or skill entry

## Delivery outcome

Expose guide overview in human and JSON modes and route a new-user skill request to the installed overview, preserving root/mirror parity and links.

## Evidence boundary

This artifact records a **proposed** claim. Its source, capture time,
and content hash are recorded in frontmatter; the claim is not implementation
evidence by itself.
