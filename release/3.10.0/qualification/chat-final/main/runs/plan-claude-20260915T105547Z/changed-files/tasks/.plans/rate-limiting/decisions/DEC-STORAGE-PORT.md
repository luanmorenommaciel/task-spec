---
schema_version: 1
kind: decision
id: DEC-STORAGE-PORT
status: proposed
owner: pending human assignment at plan review
rationale: Because no production store may be selected, counter state sits behind a storage port with
  an in-memory reference adapter used by tests. This keeps the steel thread provable without pre-empting
  the deferred infrastructure decision.
---
# DEC-STORAGE-PORT

Status: **proposed**

Owner: pending human assignment at plan review

## Rationale

Because no production store may be selected, counter state sits behind a storage port with an in-memory reference adapter used by tests. This keeps the steel thread provable without pre-empting the deferred infrastructure decision.
