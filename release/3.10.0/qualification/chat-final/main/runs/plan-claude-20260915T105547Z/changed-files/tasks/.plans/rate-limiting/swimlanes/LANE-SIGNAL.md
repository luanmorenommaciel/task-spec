---
schema_version: 1
kind: swimlane
claim: derived
id: LANE-SIGNAL
name: Decision signal lane
owner: UNASSIGNED placeholder (see DEC-OWNER-UNASSIGNED)
seam_id: SEAM-DECISION-SIGNAL
source_seam_sha256: 6ec9723980d779da4c55ef15d73cb850f61bf5ba93f02a8930abedf7454577d6
legs:
- LEG-DENIAL-REASON
- LEG-DECISION-TELEMETRY
---
# Decision signal lane

This is the single owning swimlane for `SEAM-DECISION-SIGNAL`. Ownership is `UNASSIGNED placeholder (see DEC-OWNER-UNASSIGNED)`.
Sibling capability legs are ordered only by explicit dependencies or recorded
contention—not by their position in this file.
