# Compatibility policy

Within the current major, Task-Spec reads published historical contracts and
writes the newest contract by default.

| Surface | Read | Default write |
|---|---|---|
| Task-Spec format | v1, v2, v3, v4 | v3; v4 only by explicit author choice |
| HMAC authorization | v1, v2, v3 | v3 |
| TaskHandoff | v1, v2, v3 | v3 |
| Evidence receipts | v1, v2 | v2 |
| A2A artifact | v1, v2, v3 | v3 with the A2A 1.0 data-part shape |
| MCP task bridge | v1, v2 | v2 with the stateless MCP 2026-07-28 marker |

Historical HMAC v1/v2 and receipt v1 are supervised Tier 2 because their
payloads cannot express the complete revision/attempt subject. They are not
silently upgraded. An operator reviews and restamps each active task.

A contract is removed only in a future major with retained conformance fixtures
and migration tooling. Optional MCP/A2A/DSSE adapters may negotiate transport
versions without changing the normative Task-Spec core.
