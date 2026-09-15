---
schema_version: 1
kind: decision
id: DEC-METERING-OUT-OF-SCOPE
status: accepted
owner: provider (metering remains provider-owned per the source fixture)
rationale: Usage metering stays with its provider owner and out of this scope. No leaf reads, writes,
  reconciles, or bills against metering records, and no leaf derives limits or counters from metering
  data; the limiter owns its own counter.
---
# DEC-METERING-OUT-OF-SCOPE

Status: **accepted**

Owner: provider (metering remains provider-owned per the source fixture)

## Rationale

Usage metering stays with its provider owner and out of this scope. No leaf reads, writes, reconciles, or bills against metering records, and no leaf derives limits or counters from metering data; the limiter owns its own counter.
