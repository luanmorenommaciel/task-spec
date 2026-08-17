# Frozen 3.8.1 engine benchmark

This corridor contains three sealed synthetic Task-Spec leaves and the exact
snapshot from which every engine attempt starts. `EngineMatrix/v2` allows one
attempt per engine and task. Disabled, unavailable, failed, rejected, or
scope-violating attempts remain visible and never count as passes.

| Case | Effort | Discriminating behavior |
|---|---|---|
| `xs` | XS | Create one file with one exact value |
| `s` | S | Repair human and JSON output for a small CLI |
| `m` | M | Repair dependency readiness and named cycle diagnostics |

The runner reconstructs each snapshot as a detached worktree owned by a
temporary sanitized bare repository. That repository contains no Task-Spec
signing or evaluator keys. The engine receives the frozen `TaskHandoff/v3`;
only the host-side acceptance process receives the existing repository signing
key. Large raw streams stay outside Git. The result retains their SHA-256
digests, sanitized command/environment manifests, patches, changed-file
manifests, exact observed model identifiers, duration, reported usage, and
every failure classification.

This is a release benchmark, not evidence of production reliability.
