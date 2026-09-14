---
schema_version: 1
kind: swimlane
claim: derived
id: LANE-CONTENTION
name: contention delivery
owner: pilot-contention
seam_id: SEAM-CONTENTION
source_seam_sha256: 69303c8692aa7ae42840d3ecfe1af06cf689d5f0a2fbec09588fecbcd1a03827
legs:
- LEG-CONTENTION
---
# contention delivery

This is the single owning swimlane for `SEAM-CONTENTION`. Ownership is `pilot-contention`.
Sibling capability legs are ordered only by explicit dependencies or recorded
contention—not by their position in this file.
