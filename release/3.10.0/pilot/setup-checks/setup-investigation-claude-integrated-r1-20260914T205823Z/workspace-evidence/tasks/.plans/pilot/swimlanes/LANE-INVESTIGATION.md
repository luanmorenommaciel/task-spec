---
schema_version: 1
kind: swimlane
claim: derived
id: LANE-INVESTIGATION
name: investigation delivery
owner: pilot-investigation
seam_id: SEAM-INVESTIGATION
source_seam_sha256: 98d409c585ad4dc03b7899867365ea0ca508354a74e28f63793d4f5d7b2e8209
legs:
- LEG-INVESTIGATION
---
# investigation delivery

This is the single owning swimlane for `SEAM-INVESTIGATION`. Ownership is `pilot-investigation`.
Sibling capability legs are ordered only by explicit dependencies or recorded
contention—not by their position in this file.
