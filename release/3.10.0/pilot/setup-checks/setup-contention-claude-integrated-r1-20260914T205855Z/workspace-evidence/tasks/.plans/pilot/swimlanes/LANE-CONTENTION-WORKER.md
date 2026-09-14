---
schema_version: 1
kind: swimlane
claim: derived
id: LANE-CONTENTION-WORKER
name: contention-worker delivery
owner: pilot-contention-worker
seam_id: SEAM-CONTENTION-WORKER
source_seam_sha256: f91d0d75d663e602b70ec6dc6234b37bc6ba4ac3b46707c752db875355b6b914
legs:
- LEG-CONTENTION-WORKER
---
# contention-worker delivery

This is the single owning swimlane for `SEAM-CONTENTION-WORKER`. Ownership is `pilot-contention-worker`.
Sibling capability legs are ordered only by explicit dependencies or recorded
contention—not by their position in this file.
