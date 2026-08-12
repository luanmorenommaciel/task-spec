# Trust and operational boundaries

Task-Spec narrows trust; it does not eliminate it.

| Mechanism | Proves | Does not prove |
|---|---|---|
| HMAC v2 | A holder of the shared repository key sealed this exact body and authorization envelope | Per-author identity, non-repudiation, secret safety, or sandboxing |
| PRE-gate | Structural validity, shell quality, non-trivial eval behavior, and seal tier | That future implementation is correct |
| POST-gate v3 | Current eval pass, declared blast radius, and unchanged seal | Deployment, production health, independent external receipt, or semantic perfection |
| POST-gate v4 | The v3 gates plus every policy-required receipt match the sealed task | That any evaluator or environment claim is globally complete |
| Gold sanity / eval audit | Evals fail on selected baseline/mutations and pass now | Completeness against every possible fault |
| Ed25519 identity receipt | A matching non-revoked public key signed the HMAC authorization reference | That the signer was authorized by an external organization |
| Environment receipt | A named provider asserted it enforced a contract digest | A production sandbox unless that provider actually supplies one |
| Conformance | Adapter behavior against published fixtures | Operational reliability or fleet autonomy |

Existence-only evals are rejected for blind delegation unless supervised or
explicitly annotated. Valid HMAC v1 remains authentic on its narrower historical
payload but is downgraded to Tier 2 until re-stamped with v2.

For high consequence work, format v4 can require private holdouts, an external
sandbox receipt, durable graded evidence, and accountable human authorization.
The actual sandbox, evaluator quality, and organizational authority remain
outside this repository and must be independently governed.
