---
schema_version: 1
kind: delivery-intent
id: DI-PILOT-RELEASE-EVIDENCE
title: Archive selection depends on ignore state to exclude local advisor settings
claim: proposed
source:
  uri: tests/fixtures/toolkit/pilot-issue.json
  captured_at: '2026-09-14T20:20:46.550715+00:00'
  sha256: ac848dca90458bdca62cedd9413ba4f7d9ef7ba571a0fba4be7ccf0ec2f4ee0d
success:
- Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build
  an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the
  source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported
  release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment
  health.
out_of_scope:
- Changes outside the registered write surface.
- Production deployment, policy changes, self-authorization, and independent agents.
---
# Archive selection depends on ignore state to exclude local advisor settings

## Delivery outcome

Exclude WATCHDOG.yml even if tracked or force-added, and exclude generated conformance state. Build an actual candidate archive under docs/examples/pilot-artifacts, verify its checksum, and record the source base revision plus exact artifact digest in docs/examples/pilot-release-evidence.json as reported release evidence. Explicitly disclose that candidate changes are uncommitted and do not claim deployment health.

## Evidence boundary

This artifact records a **proposed** claim. Its source, capture time,
and content hash are recorded in frontmatter; the claim is not implementation
evidence by itself.
