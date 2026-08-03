#!/usr/bin/env bash
# _lib.sh — shared helpers for the task-spec engine.
#
# Lives at src/lib/_lib.sh. Source this from every top-level script (scripts
# sit one dir below src/, so the lib is at ../lib relative to each):
#   _LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/../lib" && pwd)/_lib.sh"
#   source "$_LIB"
#
# Exports:
#   TASKSPEC_VERSION       — canonical version string (mirrors ./VERSION)
#   TASKSPEC_SKILL_DIR     — absolute path of the task-spec engine repo root
#   TASKSPEC_BACKLOG_DIR   — configurable backlog directory (default: tasks)
#
# Helpers:
#   ts_version_flag "$@"   — call ONCE at the top of arg parsing.
#                            If $1 is --version, prints "task-spec v$TASKSPEC_VERSION"
#                            and exits 0. Otherwise returns 0 silently.
#   ts_die <msg>           — print to stderr and exit 1.

# ----- Canonical version (runtime source of truth) -----
# Format change protocol:
#   1) bump TASKSPEC_VERSION here
#   2) bump ./VERSION at the repo root (must match; bin/taskspec version reads it)
#   3) add a CHANGELOG.md entry (the [x.y.z] heading must match)
#   4) bump version field in integrations/claude-code/plugin.json + marketplace.json
# The doc-consistency lint (tests/lint-skill-docs.sh) asserts (1) == (2) == (3).
TASKSPEC_VERSION="3.4.0"

# ----- Resolve the engine repo root from this file's location -----
# _lib.sh lives at src/lib/_lib.sh, so the repo root is two levels up.
# Works whether sourced from src/<verb>/ scripts or via an indirect symlink.
__lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASKSPEC_SKILL_DIR="$(cd "$__lib_dir/../.." && pwd)"
export TASKSPEC_VERSION TASKSPEC_SKILL_DIR

# ----- Configurable backlog dir (allow downstream users to override) -----
# Defaults to "tasks" relative to PWD (preserves existing behavior).
# Override per-call: TASKSPEC_BACKLOG_DIR=path/to/backlog command...
: "${TASKSPEC_BACKLOG_DIR:=tasks}"
export TASKSPEC_BACKLOG_DIR

# ----- --version handler -----
# Usage at the top of arg parsing:
#   ts_version_flag "$@"
# Call ts_version_flag BEFORE the per-script flag loop so authors can always
# discover the version without learning per-script syntax.
ts_version_flag() {
  if [[ "${1:-}" == "--version" ]]; then
    echo "task-spec v$TASKSPEC_VERSION"
    exit 0
  fi
  return 0
}

# ----- Error helper -----
ts_die() {
  echo "ERROR: $*" >&2
  exit 1
}

# ===========================================================================
# v3 — open-format helpers: profiles, A2A lifecycle, behavior/eval extraction
# ===========================================================================
# These helpers are the single source of truth for the v3 additive concepts so
# the validator, the acceptance gate, and the conformance harness agree byte-for
# -byte. All are bash-3.2-safe (no associative arrays, no mapfile).

# ----- Effort-scaled profiles (C2) -----
# A profile declares HOW MUCH of the format a spec must carry, scaling rigor with
# consequence. The profile axis is ORTHOGONAL to format_version: a v2.2 spec with
# no `profile:` field defaults to `standard` (every historical spec stays valid).
#
#   lite     — Intent (Goal) + Success Criteria + Exit Check. Behavior/Guardrails
#              optional. For S-effort, low-blast-radius work.
#   standard — lite + Behavior block + Guardrails (Anti-Patterns, Do-Not-Touch),
#              with behavior<->eval traceability enforced. The default.
#   full     — standard + Rollback + Observability. Required for anything
#              dispatched unattended (severity security/financial-critical, or any
#              L-adjacent M task).
TS_PROFILES="lite standard full"
export TS_PROFILES

# Resolve the declared profile for a spec file. Echoes lite|standard|full.
# Absent field → standard (backward-compatible default). $1 = spec path.
ts_profile() {
  local file="$1" p
  p=$(grep -m1 '^profile:' "$file" 2>/dev/null | awk '{print $2}' || true)
  case "$p" in
    lite|standard|full) printf '%s' "$p" ;;
    *)                   printf 'standard' ;;
  esac
}

# ----- A2A lifecycle mapping (C6) -----
# Map a Task-Spec status to the canonical A2A (Agent2Agent, Linux Foundation)
# TaskState enum, so a Task-Spec is interoperable with A2A-aware dispatchers.
# A2A states: submitted working input-required completed failed canceled rejected
# Our lifecycle: ready in-progress blocked done parked
#   ready       -> submitted        (acknowledged, not yet started)
#   in-progress -> working          (actively executed)
#   blocked     -> input-required    (interrupted, awaiting a human/upstream)
#   done        -> completed         (terminal success)
#   parked      -> failed            (terminal: budget exhausted / refused)
# $1 = task status. Echoes the A2A state, or 'unspecified' for an unknown status.
#
# COMPATIBILITY CONTRACT (B5): ts_a2a_state's output is the STABLE lowercase
# legacy surface (submitted|working|input-required|completed|failed). It is
# consumed verbatim by validate-task-spec.sh's success line and conformance-
# check.sh's report strings, and asserted on by tests/test-v3-closed-loop-e2e.sh
# ('A2A: submitted'). It MUST NOT change. The canonical A2A v1.0 SCREAMING_SNAKE
# enum is exposed separately by ts_a2a_state_v1 below.
ts_a2a_state() {
  case "$1" in
    ready)        printf 'submitted' ;;
    in-progress)  printf 'working' ;;
    blocked)      printf 'input-required' ;;
    done)         printf 'completed' ;;
    parked)       printf 'failed' ;;
    *)            printf 'unspecified' ;;
  esac
}

# ----- A2A v1.0 lifecycle mapping (B5 — canonical TaskState enum) -----
# Pin a Task-Spec status to the canonical A2A v1.0 TaskState enum, whose values
# are SCREAMING_SNAKE_CASE. This is the spec-accurate surface for interop with an
# A2A v1.0 dispatcher. ts_a2a_state (above) is the legacy lowercase alias kept for
# backward compatibility; this helper is the additive, non-breaking pin.
#
# A2A v1.0 TaskState members (canonical, TASK_STATE_-prefixed):
#   TASK_STATE_SUBMITTED WORKING COMPLETED FAILED CANCELED INPUT_REQUIRED
#   REJECTED AUTH_REQUIRED, plus the catch-all TASK_STATE_UNSPECIFIED.
# Task-Spec lifecycle mapping:
#   ready       -> TASK_STATE_SUBMITTED        (acknowledged, not yet started)
#   in-progress -> TASK_STATE_WORKING          (actively executed)
#   blocked     -> TASK_STATE_INPUT_REQUIRED   (interrupted, awaiting human/upstream)
#   done        -> TASK_STATE_COMPLETED        (terminal success)
#   parked      -> TASK_STATE_FAILED           (terminal: budget exhausted / refused)
# CANCELED, REJECTED, and AUTH_REQUIRED are valid A2A v1.0 states with no
# Task-Spec lifecycle source today; they are passed THROUGH if a caller supplies
# them directly (an A2A-native status), so this helper is a total function over
# the v1.0 enum as well as the Task-Spec lifecycle.
# The emitted values are the SPEC-ACCURATE A2A v1.0 enum members, which are
# TASK_STATE_-prefixed (e.g. TASK_STATE_SUBMITTED). The spec's catch-all member is
# TASK_STATE_UNSPECIFIED, so an unknown status maps there. A caller may pass either
# a Task-Spec lifecycle status OR an already-canonical TASK_STATE_* value (or its
# bare form), and the function returns the canonical prefixed member either way.
# $1 = task status (Task-Spec lifecycle OR an A2A v1.0 enum value, prefixed or bare).
# Echoes the canonical A2A v1.0 TaskState, or TASK_STATE_UNSPECIFIED if unknown.
ts_a2a_state_v1() {
  case "$1" in
    ready)                            printf 'TASK_STATE_SUBMITTED' ;;
    in-progress)                      printf 'TASK_STATE_WORKING' ;;
    blocked)                          printf 'TASK_STATE_INPUT_REQUIRED' ;;
    done)                             printf 'TASK_STATE_COMPLETED' ;;
    parked)                           printf 'TASK_STATE_FAILED' ;;
    TASK_STATE_SUBMITTED|TASK_STATE_WORKING|TASK_STATE_COMPLETED|TASK_STATE_FAILED|TASK_STATE_CANCELED|TASK_STATE_INPUT_REQUIRED|TASK_STATE_REJECTED|TASK_STATE_AUTH_REQUIRED)
                                      printf '%s' "$1" ;;
    SUBMITTED|WORKING|COMPLETED|FAILED|CANCELED|INPUT_REQUIRED|REJECTED|AUTH_REQUIRED)
                                      printf 'TASK_STATE_%s' "$1" ;;
    *)                                printf 'TASK_STATE_UNSPECIFIED' ;;
  esac
}

# ----- Frontmatter extraction (DRY: was copy-pasted in 3 scripts) -----
# Echo the YAML frontmatter BODY — every line between the opening '---' (line 1)
# and the next '---' — for a spec file. The delimiters themselves are excluded.
# This is the single source of truth; validate-task-spec.sh, accept-task.sh, and
# lint-backlog.sh all call it instead of re-implementing the awk. $1 = spec path.
ts_frontmatter() {
  awk 'NR==1 && /^---[[:space:]]*$/{s=1; next} s && /^---[[:space:]]*$/{exit} s{print}' "$1" 2>/dev/null || true
}

# ----- Behavior / eval extraction for traceability (C3/C4) -----
# Echo the behavior ids (B-1, B-2, …) declared in the ## Behavior section,
# one per line, sorted-unique. A behavior id anchors a Given/When/Then scenario.
# $1 = spec path.
ts_behavior_ids() {
  local file="$1"
  awk '/^## Behavior/{f=1; next} /^## /{f=0} f' "$file" 2>/dev/null \
    | grep -oE 'B-[0-9]+' | sort -u || true
}

# Echo every behavior id REFERENCED by a `verifies:` line anywhere in the spec
# (validation_card eval entries declare `verifies: [B-1, B-2]`). One per line,
# sorted-unique. $1 = spec path.
ts_verified_behavior_ids() {
  local file="$1"
  grep -hoE 'verifies:[[:space:]]*\[[^]]*\]' "$file" 2>/dev/null \
    | grep -oE 'B-[0-9]+' | sort -u || true
}

# ----- requires: isolation block (B3, OPTIONAL, document-and-warn) -----
# A spec MAY declare a `requires:` block in its frontmatter to tell a dispatcher
# what isolation the executor's sandbox must provide. It is purely DECLARATIVE:
# accept-task.sh READS and REPORTS it; the bash tool cannot itself enforce network
# egress. The recognized sub-keys (all optional):
#   base_image   — container/runtime image the eval set assumes
#   deps         — packages the sandbox must provision (free-form list/scalar)
#   network      — one of: deny | allow-list | open  (egress posture)
# All helpers are bash-3.2-safe (no associative arrays) and only inspect the
# frontmatter region (between the first two '---' lines), never the body.

# Return 0 if the spec has a top-level `requires:` block in its frontmatter.
# $1 = spec path.
ts_has_requires() {
  awk '
    BEGIN { in_fm=0; fmc=0; found=0 }
    /^---[[:space:]]*$/ { fmc++; if (fmc==1){in_fm=1; next} if (fmc==2){exit} }
    in_fm==1 && /^requires:[[:space:]]*$/ { found=1; exit }
    END { exit (found?0:1) }
  ' "$1"
}

# Echo the value of a sub-key under the frontmatter `requires:` block, trimmed of
# surrounding whitespace and a single layer of matching quotes. Echoes nothing
# (and the caller treats absence as "unset") when the block or key is missing.
# Only keys indented under `requires:` and before the next top-level field are
# read, so a body line that happens to start with the key name is never matched.
# $1 = spec path, $2 = sub-key name (e.g. network).
ts_requires_field() {
  local file="$1" key="$2"
  awk -v want="$key" '
    BEGIN { in_fm=0; in_req=0; fmc=0 }
    /^---[[:space:]]*$/ { fmc++; if (fmc==1){in_fm=1; next} if (fmc==2){exit} }
    in_fm==0 { next }
    /^requires:[[:space:]]*$/ { in_req=1; next }
    in_req==1 && /^[A-Za-z_]/ { in_req=0 }
    in_req==1 {
      line=$0
      sub(/^[[:space:]]+/, "", line)
      if (line ~ ("^" want ":")) {
        sub(("^" want ":[[:space:]]*"), "", line)
        sub(/[[:space:]]*$/, "", line)
        gsub(/^["'"'"']|["'"'"']$/, "", line)
        print line
        exit
      }
    }
  ' "$file"
}

# Resolve the baseline ref a gold-sanity check should diff against, in priority:
#   1. an explicit override ($2, e.g. accept-task's --base when not the default)
#   2. a frontmatter `baseline_ref:` or `reference_solution:` scalar
#   3. nothing (caller falls back to its own default, typically HEAD)
# $1 = spec path, $2 (optional) = explicit override. Echoes the ref or nothing.
ts_baseline_ref() {
  local file="$1" override="${2:-}" ref=""
  if [[ -n "$override" ]]; then printf '%s' "$override"; return 0; fi
  ref=$(grep -m1 '^baseline_ref:' "$file" 2>/dev/null | sed -E 's/^baseline_ref:[[:space:]]*//' | sed -E 's/[[:space:]]*$//' || true)
  if [[ -z "$ref" ]]; then
    ref=$(grep -m1 '^reference_solution:' "$file" 2>/dev/null | sed -E 's/^reference_solution:[[:space:]]*//' | sed -E 's/[[:space:]]*$//' || true)
  fi
  ref="${ref#\"}"; ref="${ref%\"}"; ref="${ref#\'}"; ref="${ref%\'}"
  [[ -n "$ref" ]] && printf '%s' "$ref"
  return 0
}

# ----- Portable timeout (C8 harness needs it; macOS ships no `timeout`) -----
# Run a command with a wall-clock limit. Prefers `timeout`, then `gtimeout`
# (coreutils on macOS), then a pure-bash watchdog. Exit 124 on timeout, mirroring
# GNU `timeout`. $1 = seconds; $2.. = command + args.
ts_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"; return $?
  fi
  if command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$secs" "$@"; return $?
  fi
  # Pure-bash fallback: run the command in the background, kill it if it overruns.
  "$@" &
  local cmd_pid=$!
  (
    sleep "$secs"
    kill -0 "$cmd_pid" 2>/dev/null && kill -TERM "$cmd_pid" 2>/dev/null
  ) &
  local watch_pid=$!
  local rc=0
  wait "$cmd_pid" 2>/dev/null || rc=$?
  kill -0 "$watch_pid" 2>/dev/null && kill "$watch_pid" 2>/dev/null
  wait "$watch_pid" 2>/dev/null || true
  # If the command was killed by SIGTERM, bash reports 143 (128+15) → normalize
  # to 124 so callers can detect "timed out" uniformly.
  if [[ $rc -eq 143 ]]; then rc=124; fi
  return $rc
}

# ----- Portable advisory lock (macOS ships no `flock`) -----
# `flock` is Linux util-linux and is absent on macOS — the maintainers' own
# platform. These helpers provide a cross-platform mutual-exclusion primitive
# using an atomic `mkdir` (POSIX-atomic on every platform), mirroring how
# ts_timeout guards the missing `timeout`.
#
# ts_lock_acquire <lockfile>  — atomically create a lock dir at "<lockfile>.d".
#   Returns 0 if the caller now holds the lock, 1 if another process holds it.
#   A stale lock (no live holder) older than TS_LOCK_STALE_SEC (default 120) is
#   reclaimed so a crashed holder never deadlocks the backlog.
# ts_lock_release <lockfile> — remove the lock dir (best-effort).
# Both are no-ops-safe: releasing an unheld lock returns 0.
: "${TS_LOCK_STALE_SEC:=120}"
ts_lock_acquire() {
  local d="${1}.d"
  if mkdir "$d" 2>/dev/null; then
    printf '%s' "$$" > "$d/pid" 2>/dev/null || true
    return 0
  fi
  # Lock dir exists — check whether the holder is alive / the lock is stale.
  local holder age now mtime
  holder="$(cat "$d/pid" 2>/dev/null || true)"
  if [[ -n "$holder" ]] && kill -0 "$holder" 2>/dev/null; then
    return 1   # a live process holds it
  fi
  # No live holder, or no pid recorded: reclaim if older than the stale window.
  now="$(date +%s 2>/dev/null || echo 0)"
  mtime="$(stat -f %m "$d" 2>/dev/null || stat -c %Y "$d" 2>/dev/null || echo 0)"
  age=$(( now - mtime ))
  if [[ "$now" -gt 0 && "$mtime" -gt 0 && "$age" -ge "$TS_LOCK_STALE_SEC" ]]; then
    rm -rf "$d" 2>/dev/null
    if mkdir "$d" 2>/dev/null; then
      printf '%s' "$$" > "$d/pid" 2>/dev/null || true
      return 0
    fi
  fi
  return 1
}
ts_lock_release() {
  rm -rf "${1}.d" 2>/dev/null
  return 0
}

# ----- Safe temp-target preparation (symlink-attack hardening) -----
# The in-place editors write to a predictable sibling temp path ("<file>.tmp.$$"
# / ".fmset.$$") then mv it over the original. A shell redirect `> "$tmp"`
# FOLLOWS a pre-existing symlink at that path, which an attacker with write
# access to the directory could plant to clobber an arbitrary target. Call this
# immediately before redirecting into a predictable temp path: it removes any
# pre-existing file/symlink at that path so the redirect creates a fresh regular
# file. $1 = the temp path. Returns 0 (best-effort rm; a still-present path is
# caught by the caller's post-write checks).
ts_prepare_tmp() {
  rm -f "$1" 2>/dev/null
  return 0
}

# ===========================================================================
# B2 — key-optional HMAC sign-off envelope (v2.2)
# ===========================================================================
# These helpers implement the cryptographic floor for the sign-off envelope.
# They are intentionally key-optional and crypto-binary-optional: a fresh
# clone with no key, or a minimal CI image with no openssl, MUST degrade to
# structural-only (Tier 2) rather than hard-fail. See the three-tier contract
# in references/concepts/signed-off.md.
#
# Portability floor (REQUIREMENT 3):
#   ts_sha256        — sha256 over stdin; detects openssl > shasum -a 256 > sha256sum.
#                      Prints the hex digest. Returns 0 on success; prints the
#                      sentinel TS_CRYPTO_UNAVAILABLE and returns 0 (callers treat
#                      that string as "no crypto" and fall to Tier 2) when none
#                      of the three providers exists.
#   ts_hmac_sha256   — HMAC-SHA256(key, message). Prefers `openssl dgst -sha256
#                      -hmac KEY`; if only a plain sha256 tool is present,
#                      constructs HMAC manually via the RFC-2104 ipad/opad
#                      construction (block size 64) so the result is byte-for-byte
#                      identical to openssl. Emits TS_CRYPTO_UNAVAILABLE when no
#                      sha256 provider exists.
#
# All HMAC inputs treat the key as LITERAL STRING BYTES (matching openssl's
# `-hmac KEY` default), NOT as decoded hex. This keeps the manual and openssl
# paths interchangeable.

TS_CRYPTO_UNAVAILABLE="TS_CRYPTO_UNAVAILABLE"

# Detect a sha256 provider once. Echoes one of: openssl|shasum|sha256sum|none
# Each candidate is PROBE-RUN (not just `command -v`) so a masked/stub binary
# that is on PATH but non-functional is treated as absent — this is what makes
# PATH-masking the three tools degrade cleanly to the sentinel (Tier 2) instead
# of detecting a tool that then fails at runtime.
ts_sha256_provider() {
  local probe="ts-probe"
  if command -v openssl >/dev/null 2>&1 \
     && printf '%s' "$probe" | openssl dgst -sha256 >/dev/null 2>&1; then
    echo openssl; return 0
  fi
  if command -v shasum >/dev/null 2>&1 \
     && printf '%s' "$probe" | shasum -a 256 >/dev/null 2>&1; then
    echo shasum; return 0
  fi
  if command -v sha256sum >/dev/null 2>&1 \
     && printf '%s' "$probe" | sha256sum >/dev/null 2>&1; then
    echo sha256sum; return 0
  fi
  echo none
}

# sha256 hex of stdin. Never hard-fails; emits the sentinel when no provider.
ts_sha256() {
  local provider
  provider="$(ts_sha256_provider)"
  case "$provider" in
    openssl)   openssl dgst -sha256 2>/dev/null | sed 's/^.*= //' ;;
    shasum)    shasum -a 256 | awk '{print $1}' ;;
    sha256sum) sha256sum | awk '{print $1}' ;;
    *)         printf '%s\n' "$TS_CRYPTO_UNAVAILABLE" ;;
  esac
}

# Internal: hex-encode stdin without requiring xxd (od is POSIX-portable).
ts__to_hex() { od -An -v -tx1 | tr -d ' \n'; }

# Internal: decode a hex string ($1) to raw bytes on stdout without xxd.
ts__from_hex() {
  local hex="$1" out="" i
  for (( i=0; i<${#hex}; i+=2 )); do out+="\\x${hex:i:2}"; done
  printf '%b' "$out"
}

# Internal: sha256 hex of stdin using the plain-tool providers only (shasum /
# sha256sum / openssl dgst). Used by the manual HMAC fallback.
ts__sha256_plain() {
  local provider
  provider="$(ts_sha256_provider)"
  case "$provider" in
    openssl)   openssl dgst -sha256 2>/dev/null | sed 's/^.*= //' ;;
    shasum)    shasum -a 256 | awk '{print $1}' ;;
    sha256sum) sha256sum | awk '{print $1}' ;;
    *)         printf '%s\n' "$TS_CRYPTO_UNAVAILABLE" ;;
  esac
}

# Internal: RFC-2104 HMAC-SHA256 built from a plain sha256 tool, byte-for-byte
# identical to `openssl dgst -sha256 -hmac KEY`. $1=key (literal bytes), reads
# the message from stdin. Block size 64. Keys >64 bytes are hashed first.
ts__hmac_manual() {
  local key="$1" msg keyhex keylen blocksize=64
  msg="$(cat)"
  keyhex=$(printf '%s' "$key" | ts__to_hex)
  keylen=$(( ${#keyhex} / 2 ))
  if (( keylen > blocksize )); then
    keyhex=$(printf '%s' "$key" | ts__sha256_plain)
    keylen=32
  fi
  local padcount=$(( (blocksize - keylen) * 2 ))
  if (( padcount > 0 )); then
    keyhex="${keyhex}$(printf '0%.0s' $(seq 1 "$padcount"))"
  fi
  local i ipad="" opad="" b
  for (( i=0; i<${#keyhex}; i+=2 )); do
    b=$(( 16#${keyhex:i:2} ))
    ipad+=$(printf '%02x' $(( b ^ 0x36 )))
    opad+=$(printf '%02x' $(( b ^ 0x5c )))
  done
  local inner
  inner=$( { ts__from_hex "$ipad"; printf '%s' "$msg"; } | ts__sha256_plain )
  { ts__from_hex "$opad"; ts__from_hex "$inner"; } | ts__sha256_plain
}

# HMAC-SHA256. $1=key (literal bytes). Reads message from stdin. Emits hex.
# Prefers openssl; otherwise constructs HMAC manually via RFC-2104. Emits the
# sentinel TS_CRYPTO_UNAVAILABLE when no sha256 provider exists.
ts_hmac_sha256() {
  local key="$1" provider
  provider="$(ts_sha256_provider)"
  case "$provider" in
    openssl)
      openssl dgst -sha256 -hmac "$key" 2>/dev/null | sed 's/^.*= //'
      ;;
    shasum|sha256sum)
      ts__hmac_manual "$key"
      ;;
    *)
      printf '%s\n' "$TS_CRYPTO_UNAVAILABLE"
      ;;
  esac
}

# ----- Sign-off key resolution (REQUIREMENT 4) -----
# Resolve the repository signing key, in priority order:
#   1. TASKSPEC_SIGNING_KEY env var:
#        - if it names a readable FILE, read the key material from it;
#        - otherwise use the value DIRECTLY as raw key material.
#   2. <git-dir>/info/taskspec-signing-key, where <git-dir> is whatever
#      `git rev-parse --git-dir` resolves to from the spec's location. In a
#      normal clone that is `.git`; in a linked WORKTREE `.git` is a file but
#      git resolves it to the per-worktree gitdir (…/.git/worktrees/<name>), so
#      the key IS found there too. The path is used only when that resolved
#      gitdir is a real directory AND the key file exists inside its info/.
#      A relative gitdir is canonicalized to absolute first.
#   3. otherwise: no key (prints nothing, returns 1 → caller degrades to Tier 2).
#
# Key material is trimmed of surrounding whitespace/newlines so a key file
# written with a trailing newline still produces a stable MAC.
# $1 (optional): a path used to locate the git dir (defaults to PWD).
ts_resolve_signing_key() {
  local anchor="${1:-$PWD}" key=""
  if [[ -n "${TASKSPEC_SIGNING_KEY:-}" ]]; then
    if [[ -f "$TASKSPEC_SIGNING_KEY" && -r "$TASKSPEC_SIGNING_KEY" ]]; then
      key="$(cat "$TASKSPEC_SIGNING_KEY")"
    else
      key="$TASKSPEC_SIGNING_KEY"
    fi
  else
    local anchor_dir git_dir
    if [[ -d "$anchor" ]]; then anchor_dir="$anchor"; else anchor_dir="$(dirname "$anchor")"; fi
    git_dir="$(cd "$anchor_dir" 2>/dev/null && git rev-parse --git-dir 2>/dev/null || true)"
    if [[ -n "$git_dir" ]]; then
      if [[ "$git_dir" != /* ]]; then
        git_dir="$(cd "$anchor_dir" 2>/dev/null && cd "$git_dir" 2>/dev/null && pwd || true)"
      fi
      if [[ -n "$git_dir" && -d "$git_dir" && -f "$git_dir/info/taskspec-signing-key" ]]; then
        key="$(cat "$git_dir/info/taskspec-signing-key")"
      fi
    fi
  fi
  key="${key#"${key%%[![:space:]]*}"}"
  key="${key%"${key##*[![:space:]]}"}"
  if [[ -z "$key" ]]; then
    return 1
  fi
  printf '%s' "$key"
  return 0
}

# keyid = first 8 hex of sha256(key). Stable short fingerprint that a stamp can
# carry so a verifier can confirm it is checking against the same key.
ts_keyid() {
  local key="$1" digest
  digest="$(printf '%s' "$key" | ts_sha256)"
  if [[ "$digest" == "$TS_CRYPTO_UNAVAILABLE" ]]; then
    printf '%s' "nokeyid"
    return 0
  fi
  printf '%s' "${digest:0:8}"
}

# ----- Injection-safe frontmatter field writer (REQUIREMENT 1 integrity) -----
# Set a frontmatter field to an EXACT value, carrying any byte literally.
# Rewrites the first existing `<name>:` line inside the frontmatter block; if the
# field is absent, injects `<name>: <value>` immediately before the closing '---'.
#
# CRITICAL: the value is passed to awk via the PROCESS ENVIRONMENT
# (ENVIRON["TS_FMSET_VAL"]), NEVER via `awk -v` and NEVER through a sed
# substitution. `awk -v` runs C-string escape processing on the assignment, so a
# value containing the two characters backslash+n would be expanded into a real
# newline and inject a forged extra frontmatter line — even though no newline
# BYTE was present. ENVIRON[] does NO escape processing, so every byte is carried
# verbatim. This is the single serialization path used to stamp signed_off,
# signed_off_by (user/CI-controlled), signed_off_at, and signed_off_sig. A value
# containing `|`, `&`, `\`, a literal `:`, a backslash-n sequence, a tab, or any
# other byte is written verbatim. Only frontmatter (the region between the first
# two '---' lines) is touched; a body line that happens to start with `<name>:`
# is never rewritten.
#
# $1=file  $2=field name  $3=field value.  Edits the file in place (temp+mv,
# portable across BSD and GNU). The file is left UNTOUCHED on any failure.
# Returns:
#   0  the field was written (rewritten in place or injected before closing ---)
#   2  the value contains a real newline or carriage-return BYTE — REJECTED. A
#      YAML scalar written this way must be single-line. (Belt-and-suspenders:
#      ENVIRON[] already prevents escape-driven injection; this guard rejects a
#      genuine embedded newline byte before it reaches the file.)
#   1  no writable frontmatter found — the file has no closing '---', so there is
#      nowhere to inject. The caller MUST hard-fail rather than HMAC a spec whose
#      field was silently not written.
# The field NAME ($2) is script-controlled (never user input) and is passed via
# -v because it is used as a regex anchor; the VALUE is the untrusted channel.
ts_set_frontmatter_field() {
  local file="$1" fname="$2" fval="$3" tmp rc
  case "$fval" in
    *$'\n'*|*$'\r'*)
      echo "ts_set_frontmatter_field: refusing multi-line value for '$fname' (newline/CR not allowed in a frontmatter scalar)" >&2
      return 2
      ;;
  esac
  tmp="${file}.fmset.$$"
  ts_prepare_tmp "$tmp"
  # awk exits 0 if the field was written, 3 if the frontmatter had no closing
  # '---' (field could not be placed). Any other awk failure also leaves the
  # original untouched. The value comes from ENVIRON (verbatim); only fname is -v.
  TS_FMSET_VAL="$fval" awk -v fname="$fname" '
    BEGIN { fm_count=0; in_fm=0; done=0; fval=ENVIRON["TS_FMSET_VAL"] }
    /^---[[:space:]]*$/ {
      fm_count++
      if (fm_count == 1) { in_fm=1; print; next }
      if (fm_count == 2) {
        if (in_fm == 1 && done == 0) { print fname ": " fval; done=1 }
        in_fm=0
        print
        next
      }
      print; next
    }
    {
      if (in_fm == 1 && done == 0 && $0 ~ ("^" fname ":")) {
        print fname ": " fval
        done=1
        next
      }
      print
    }
    END { if (done == 0) exit 3 }
  ' "$file" > "$tmp"
  rc=$?
  if [[ $rc -ne 0 ]]; then
    rm -f "$tmp"
    [[ $rc -eq 3 ]] && echo "ts_set_frontmatter_field: no closing '---' frontmatter delimiter in $file; '$fname' not written" >&2
    return 1
  fi
  mv "$tmp" "$file"
}

# ----- Canonical sign-off payload (REQUIREMENT 1 boundary) -----
# Extract the spec BODY = everything AFTER the closing '---' of the frontmatter.
# Line 1 is the opening '---'; the body starts after the SECOND '---'.
ts_spec_body() {
  local file="$1"
  awk '
    BEGIN { fm=0 }
    NR==1 && /^---[[:space:]]*$/ { fm=1; next }
    fm==1 && /^---[[:space:]]*$/ { fm=2; next }
    fm==2 { print }
  ' "$file"
}

# sha256 hex of the spec body. Emits the sentinel when no crypto provider.
ts_body_digest() {
  ts_spec_body "$1" | ts_sha256
}

# Build the CANONICAL signed payload: newline-joined, fixed field order:
#   id=<id>
#   body_digest=<sha256 hex of body>
#   signed_off=<value>
#   signed_off_by=<value>
#   signed_off_at=<value>
# CRITICAL BOUNDARY: this reads the three signed_off* VALUES as they appear in
# the frontmatter and EXCLUDES the signed_off_sig line itself. It does NOT
# depend on frontmatter line ordering — each field is grepped by name. This is
# what makes the MAC verify on the very next read after stamping.
# $1=file. Echoes the payload (no trailing newline) on stdout.
ts_signoff_payload() {
  local file="$1"
  local id body_digest so so_by so_at
  id=$(grep -m1 '^id:' "$file" | sed -E 's/^id:[[:space:]]*//' | sed -E 's/[[:space:]]*$//')
  body_digest=$(ts_body_digest "$file")
  so=$(grep -m1 '^signed_off:' "$file" | sed -E 's/^signed_off:[[:space:]]*//' | sed -E 's/[[:space:]]*$//')
  so_by=$(grep -m1 '^signed_off_by:' "$file" | sed -E 's/^signed_off_by:[[:space:]]*//' | sed -E 's/[[:space:]]*$//')
  so_at=$(grep -m1 '^signed_off_at:' "$file" | sed -E 's/^signed_off_at:[[:space:]]*//' | sed -E 's/[[:space:]]*$//')
  printf 'id=%s\nbody_digest=%s\nsigned_off=%s\nsigned_off_by=%s\nsigned_off_at=%s' \
    "$id" "$body_digest" "$so" "$so_by" "$so_at"
}

# Compute the full signed_off_sig field value for a spec, given a key.
# Format: hmac-sha256-v1:<keyid>:<hex>
# Echoes the value; returns 1 (and echoes nothing) if crypto is unavailable.
ts_compute_signoff_sig() {
  local file="$1" key="$2" payload keyid mac
  payload="$(ts_signoff_payload "$file")"
  if [[ "$payload" == *"$TS_CRYPTO_UNAVAILABLE"* ]]; then
    return 1
  fi
  mac="$(printf '%s' "$payload" | ts_hmac_sha256 "$key")"
  if [[ "$mac" == "$TS_CRYPTO_UNAVAILABLE" || -z "$mac" ]]; then
    return 1
  fi
  keyid="$(ts_keyid "$key")"
  printf 'hmac-sha256-v1:%s:%s' "$keyid" "$mac"
  return 0
}

# ----- bash 4+ guard -----
# Some aux scripts (lint-backlog.sh, query-metrics.sh) use associative arrays
# (declare -A) and mapfile/readarray, which require bash 4+. macOS ships the
# GPL-2 system bash 3.2.57 at /bin/bash, where these constructs hard-fail with
# "declare: -A: invalid option". The core gate path (validate-task-spec.sh,
# safe-to-delegate.sh, run-task-spec.sh, _lib.sh) stays bash-3.2-clean; only
# these two aux scripts need this guard.
#
# Behavior:
#   - If the running bash is already 4+, return silently.
#   - Otherwise, look for a bash 4+ on PATH and re-exec the calling script
#     under it (preserving "$@"). $TS_BASH4_REEXEC guards against re-exec loops.
#   - If no bash 4+ is found, print a one-line remediation and exit 3.
ts_require_bash4() {
  if [[ "${BASH_VERSINFO[0]:-0}" -ge 4 ]]; then
    return 0
  fi

  if [[ -n "${TS_BASH4_REEXEC:-}" ]]; then
    echo "task-spec: requires bash 4+; on macOS run: brew install bash, then re-run this script with that bash" >&2
    exit 3
  fi

  local candidate candidate_major
  candidate="$(command -v bash 2>/dev/null || true)"
  if [[ -n "$candidate" ]]; then
    candidate_major="$("$candidate" -c 'echo "${BASH_VERSINFO[0]}"' 2>/dev/null || echo 0)"
    if [[ "$candidate_major" -ge 4 && "$candidate" != "${BASH:-}" ]]; then
      export TS_BASH4_REEXEC=1
      exec "$candidate" "${BASH_SOURCE[1]:-$0}" "$@"
    fi
  fi

  echo "task-spec: requires bash 4+; on macOS run: brew install bash, then re-run this script with that bash" >&2
  exit 3
}
