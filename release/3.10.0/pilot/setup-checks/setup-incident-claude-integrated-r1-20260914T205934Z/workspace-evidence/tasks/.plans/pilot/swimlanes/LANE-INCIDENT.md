---
schema_version: 1
kind: swimlane
claim: derived
id: LANE-INCIDENT
name: incident delivery
owner: pilot-incident
seam_id: SEAM-INCIDENT
source_seam_sha256: 4d13ca4f4eeb0b487642640f3050f78df75b1bd8b16234532060362067649f3e
legs:
- LEG-INCIDENT
---
# incident delivery

This is the single owning swimlane for `SEAM-INCIDENT`. Ownership is `pilot-incident`.
Sibling capability legs are ordered only by explicit dependencies or recorded
contention—not by their position in this file.
