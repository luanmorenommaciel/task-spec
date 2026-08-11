# Trust and operational boundaries

Task-Spec narrows trust; it does not eliminate it.

| Mechanism | Proves | Does not prove |
|---|---|---|
| HMAC v2 | A holder of the shared repository key sealed this exact body and authorization envelope | Per-author identity, non-repudiation, secret safety, or sandboxing |
| PRE-gate | Structural validity, shell quality, non-trivial eval behavior, and seal tier | That future implementation is correct |
| POST-gate | Current eval pass, declared blast radius, and unchanged seal | Deployment, production health, independent external receipt, or semantic perfection |
| Gold sanity | Evals fail on a selected unpatched baseline and pass now | Completeness against private holdouts |
| Conformance | Adapter behavior against published fixtures | Operational reliability or fleet autonomy |

Existence-only evals are rejected for blind delegation unless supervised or
explicitly annotated. Valid HMAC v1 remains authentic on its narrower historical
payload but is downgraded to Tier 2 until re-stamped with v2.

For high consequence work, add independent private holdouts, enforced sandbox
policy, fail-closed metering, durable receipts, and human authorization outside
this repository.
