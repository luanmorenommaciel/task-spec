# Runbook: Your first 10 minutes with task-spec

> **Use when:** You've just installed the skill (or are evaluating it) and want to ship a `signed_off: true` Task-Spec end-to-end on your first attempt.

This walkthrough takes you from zero to a stamped spec via the canonical three-command flow: **generate → validate → gate**. Every step is copy-pasteable. Total time: ~10 minutes.

If you finish this walkthrough and have a `signed_off: true` spec in your tempdir, the skill is correctly installed and you can move to your real backlog with confidence.

---

## Step 0 — Prerequisites

You need:

- `bash` ≥ 4.0 (macOS users: the system `/bin/bash` is 3.2; install `bash` via Homebrew or use `zsh` for the demo and bash for the scripts)
- `git` ≥ 2.20
- `python3` (used by the test suite oracle parser)
- A writable directory you can throw away after the demo

You do NOT need: Claude Code, Kimi, Codex, Tavily, Context7, or any external service. This walkthrough is **fully local**.

---

## Step 1 — Install the CLI into a fresh tempdir

```bash
ENGINE=$(mktemp -d)/task-spec
git clone --quiet https://github.com/luanmorenommaciel/task-spec.git "$ENGINE"
export PATH="$ENGINE/bin:$PATH"

TMP=$(mktemp -d)
cd "$TMP"
git init --quiet
```

Verify the install:

```bash
taskspec doctor
taskspec version
# 3.7.0
```

If the version doesn't match, you're running an older copy — check `which taskspec`.

(Optionally, install the task-architect agent + thin skill into a repo:
`bash "$ENGINE/src/lib/install.sh" --target "$TMP"`. The CLI needs no install
beyond PATH.)

---

## Step 2 — (Optional) Configure your backlog directory

By default the skill writes to `tasks/` relative to the current directory. If your project's backlog lives elsewhere:

```bash
export TASKSPEC_BACKLOG_DIR="$TMP/backlog"
mkdir -p "$TASKSPEC_BACKLOG_DIR"
```

For this walkthrough we'll use the default.

---

## Step 3 — GENERATE a spec from intent

```bash
cd "$TMP"
taskspec new add-health-endpoint S any "first-spec walkthrough"
```

You should see:

```
Spec written: /tmp/.../tasks/T-20260602-add-health-endpoint.md
  status: ready  format: 3  outdir: /tmp/.../tasks  task_spec_version: 3.7.0

Next steps:

  1. Fill in the {{TODO}} stubs:
     - title
     - touches_paths
     ...

  2. VALIDATE (pre-gate structural linter — does NOT stamp signed_off):
     bash <engine>/src/gate/validate-task-spec.sh tasks/T-20260602-add-health-endpoint.md

Next: bash <engine>/src/gate/safe-to-delegate.sh --stamp tasks/T-20260602-add-health-endpoint.md
...

  3. DISPATCH (after the gate stamps signed_off:true):
     See docs/runbooks/dispatching-a-task-spec.md ...
```

Note the **breadcrumb**: the `Next: ...safe-to-delegate.sh --stamp ...` line tells you the exact gate command for THIS specific spec.

---

## Step 4 — Fill in the stubs

Open the generated file in your editor:

```bash
$EDITOR tasks/T-*.md
```

Replace every `{{TODO}}` placeholder. At minimum:

- `title:` → human-readable name
- `touches_paths:` → real files you'll modify (must exist; use `creates_paths:` for new files)
- `## Goal` → one paragraph
- `## Context` → ≤100 lines of background
- `eval_1`, `eval_2`, `eval_3` → runnable bash that returns 0 = pass
- `## Anti-Patterns` → 3+ specific "don'ts" with reasons
- `## Do-Not-Touch` → files the executor must not modify

### ⚠️ The inverted-grep-c footgun

The single most-common eval bug in v2.0 (closed by v2.1's static lint) was:

```bash
# WRONG — produces "0\n0" on zero matches, silently INVERTS success
eval_1() {
  count=$(grep -c 'PATTERN' file || echo 0)
  [ "$count" -eq 0 ]
}

# RIGHT — exits 0 when grep finds zero matches, 1 otherwise
eval_1() {
  ! grep -q 'PATTERN' file
}
```

v2.1's validator rejects the wrong form. See [../patterns/runnable-bash-evals.md](../patterns/runnable-bash-evals.md) for the full foot-gun catalog.

---

## Step 5 — VALIDATE (pre-gate structural linter)

```bash
taskspec validate tasks/T-*.md
```

Expected output:

```
OK: tasks/T-20260602-add-health-endpoint.md is a valid Task-Spec v3 (profile: standard → A2A: submitted)
```

If you see `FAIL:`, fix the listed errors and re-run. Common errors:

- `unfilled {{TODO}} placeholder(s) remain` — you missed a stub
- `touches_paths entry does not exist` — declare under `creates_paths` if greenfield
- `inverted grep -c pattern` — see Step 4's foot-gun

**Validate is NOT the gate.** It only checks structure. `signed_off:` is still `false` after this step. Continue to Step 6.

---

## Step 6 — GATE (the autonomy contract)

```bash
taskspec gate --stamp tasks/T-*.md
```

Expected output:

```
safe-to-delegate: tasks/T-20260602-add-health-endpoint.md
────────────────────────────────────────────────────────
1. Structural validation + shellcheck-evals ...
   PASS — structurally valid, shellcheck clean
2. Eval execution (broken-logic guard) ...
   PASS — evals execute cleanly (0 pass / 3 fail; fails are expected for unbuilt work)
────────────────────────────────────────────────────────
VERDICT: DELEGATE — safe to hand off blind.
   stamped signed_off: true by $USER at 2026-06-02T18:42:00Z
```

The gate now wrote `signed_off: true` to the frontmatter. Verify:

```bash
grep '^signed_off' tasks/T-*.md
# signed_off: true
# signed_off_by: <your-user>
# signed_off_at: 2026-06-02T18:42:00Z
```

**Do not hand-edit these fields.** The v2.1 validator's structural sign-off envelope check rejects hand-stamped specs. See [../concepts/signed-off.md](../concepts/signed-off.md).

---

## Step 7 — DISPATCH (or stop here for the walkthrough)

A `signed_off: true` spec is ready to hand to an autonomous engine. The dispatch step depends on which engine you're using; start at the router [dispatching-a-task-spec.md](dispatching-a-task-spec.md) and jump to your engine's recipe under [../adapters/engines/](../../adapters/engines/).

If you got this far, **the skill is correctly installed and your first spec is signed off**. You can now:

1. Use this as a template for real specs in your project's `tasks/` directory.
2. Run `bash tests/test-task-spec-skill.sh --suite fixtures` in the engine repo to verify the lint suite.
3. Clean up the tempdir: `rm -rf "$TMP"`.

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| older `task-spec vX.Y.Z` from `--version` | Old install path is shadowing | `which taskspec` — reinstall the pinned 3.7 copy or call by absolute path |
| `OK: ...v2` on a generated spec | A v2 spec (or an older generator) — default freshly generated specs are `format_version: 3` | Cosmetic for a real v2 spec; regenerate with the 3.7 engine if you expected v3, or pass `--format 4` explicitly |
| `FAIL: signed_off: true but signed_off_by is empty` | You hand-edited `signed_off:` to `true` | Set it back to `false`; run the gate to stamp properly |
| `inverted grep -c pattern: ...` | An eval uses the foot-gun | Replace with `! grep -q PATTERN file` (see Step 4) |
| `flock: command not found` (macOS) | Missing `flock(1)` on default macOS | The test harness ships a shim; for direct script calls install via `brew install util-linux` |

---

## See also

- [dispatching-a-task-spec.md](dispatching-a-task-spec.md) — after the gate stamps, how to dispatch per `execution_backend`
- [validating-a-task-spec.md](validating-a-task-spec.md) — pre-gate linter deep dive
- [../concepts/signed-off.md](../concepts/signed-off.md) — the autonomy contract
- [../patterns/runnable-bash-evals.md](../patterns/runnable-bash-evals.md) — the full eval foot-gun catalog
- [from-fuzzy-intent.md](from-fuzzy-intent.md) — paragraph → spec without the generator
- [from-meeting-note.md](from-meeting-note.md) — Krisp output → spec
