---
schema_version: 1
kind: delivery-intent
id: DI-PILOT-CONTENTION
title: Shared-resource conflicts across independent runs lack an end-to-end regression scenario
claim: proposed
source:
  uri: tests/fixtures/toolkit/pilot-issue.json
  captured_at: '2026-09-14T20:20:46.550715+00:00'
  sha256: d3a1c617111eeccd8446a31b0a2a86a61674f7b972c8a0e5ab67c06de1a1eac8
success:
- Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second
  run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease
  authority and target branch state.
out_of_scope:
- Changes outside the registered write surface.
- Production deployment, policy changes, self-authorization, and independent agents.
---
# Shared-resource conflicts across independent runs lack an end-to-end regression scenario

## Delivery outcome

Add an isolated end-to-end regression where disjoint file changes claim one exclusive resource, a second run refuses the live conflict, and the resource becomes available after cancellation. Preserve one lease authority and target branch state.

## Evidence boundary

This artifact records a **proposed** claim. Its source, capture time,
and content hash are recorded in frontmatter; the claim is not implementation
evidence by itself.
