# Security policy

## Supported versions

Report vulnerabilities against the current `3.9.x` engine. Older tags are
frozen evidence, not a maintained security branch.

## How to report

Use GitHub private vulnerability reporting on this repository. Do not file a
public issue or pull request that includes exploit details, key material, or
a working attack.

If private reporting is unavailable, email the maintainer listed in
[package.json](package.json) and [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json).

## What is in scope

- Bypass or forgery of HMAC v3 authorization or POST-gate acceptance
- Leak or misuse of the repository signing key or evaluator private keys
  through the engine, installer, or TaskMesh helper
- Path-escape, symlink, or blast-radius failures in the acceptance Git checks
- Privilege or isolation failures on the autonomous TaskMesh worker path
- Tampering with digest-pinned release evidence so a stale tree still verifies

## What is not a vulnerability

- A weak or existence-only eval that an authorized task chose to accept
- An executor ignoring a handoff (the gates exist because executors are
  untrusted)
- TaskMesh supervised worktrees described as if they were sandboxes — they
  are not; see [docs/trust/threat-model.md](docs/trust/threat-model.md)
- HMAC proving human identity or non-repudiation (it does not)

HMAC keys and evaluator private keys must stay outside the executor
environment. The threat model and TaskMesh trust boundaries in
[docs/trust/](docs/trust/index.md) are the authoritative limits.
