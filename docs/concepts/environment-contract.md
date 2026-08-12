# Environment contracts

`requires:` describes what an executor needs. `EnvironmentContract/v1` makes a
portable enforcement target explicit:

```json
{
  "contract": "EnvironmentContract/v1",
  "runtime": {"name": "python", "version": "3.12"},
  "network": {"mode": "deny"},
  "filesystem": {"workspace": ".", "writes": ["src/", "tests/"]},
  "limits": {"timeout_sec": 900}
}
```

The frontmatter references the canonical digest. A sandbox, CI runner, or
orchestrator enforces it and emits `EnvironmentReceipt/v1`. Task-Spec verifies
the receipt-to-policy binding; it does not pretend that a host process became
isolated because a file says `enforced: true`.

Never put credentials in either contract or receipt. Authentication belongs to
the environment or secret manager outside the handoff.
