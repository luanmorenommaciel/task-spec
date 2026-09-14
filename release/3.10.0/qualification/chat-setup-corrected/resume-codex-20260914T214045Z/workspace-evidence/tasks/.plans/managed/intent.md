---
schema_version: 1
kind: delivery-intent
id: DI-RATE-LIMIT
title: Enforce organization-level request limits with visible decisions
claim: proposed
source:
  uri: tests/fixtures/toolkit/blueprint.md
  captured_at: '2026-08-02T00:00:00Z'
  sha256: f40ed16c2898b8363dfce1c19e7c3fd539d52810d52b21faeaf59323117af445
success:
- a.txt contains completed and b.txt remains empty
out_of_scope:
- Replacing provider-owned usage metering.
- Choosing production storage or deployment infrastructure.
---
# Enforce organization-level request limits with visible decisions

## Delivery outcome

Produce an exact completion artifact while preserving the sibling file.

## Evidence boundary

This artifact records a **proposed** claim. Its source, capture time,
and content hash are recorded in frontmatter; the claim is not implementation
evidence by itself.
