# Threat model

## Protected assets

- the exact work authority reviewed by a human;
- author/verifier HMAC material and evaluator private keys;
- attempt-specific evidence and acceptance decisions;
- repository paths outside the authorized write surface;
- dependency and composition meaning across replans.

## Adversary

An executor may read the public task and handoff, write anywhere its operating
environment permits, create symlinks, stage or commit changes, replay old
receipts, edit policy, rewrite history, or try to mark itself accepted. It may
know Task-Spec's implementation.

Task-Spec does not defend against an executor that can read the repository HMAC
key, evaluator private keys, or verifier process memory. Those secrets must be
kept outside its environment by the harness or sandbox.

## Fail-closed controls

| Attack | Control |
|---|---|
| Change authority after sign-off | HMAC v3 over `TaskRevision/v1` |
| Add a future unsealed field | Complete manifest with explicit mutable exclusions |
| Downgrade v4 policy to v3 | `format_version` and policy are sealed |
| Replay evidence | `ReceiptSubject/v1` binds revision, authorization, attempt, and base |
| Hide scope expansion in a commit | Diff union from handoff base through HEAD plus index/worktree/untracked |
| Rebase away the handoff base | Ancestor check fails with `BASE_DIVERGED` |
| Escape through symlinks or traversal | Existing-path and creation-parent realpath checks |
| Change dependency meaning | Signed dependency-closure digest fails with `CLOSURE_DRIFT` |
| Partially write acceptance | atomic record, mkdir locks, atomic task replacement, idempotent retry |
| Forge portable evaluator evidence | receipt-class-scoped Ed25519 trust registry |

## Residual risks

- A weak eval can still reward the wrong behavior.
- A trusted evaluator or human can be mistaken or malicious.
- HMAC key holders can create valid repository authorizations.
- Local structural receipts do not prove environmental isolation.
- Filesystem and Git checks do not prove deployed or production behavior.
- External orchestration, credentials, scheduling, and sandbox enforcement are
  outside the core.

Use narrow tasks, discriminatory evals, external keys, real sandbox evidence,
and accountable human review in proportion to consequence.
