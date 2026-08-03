#!/usr/bin/env bash
# safe-to-delegate.sh — single pre-delegation gate for a Task-Spec.
#
# Composes the existing validator + runner into one go/no-go verdict so the
# eval-discipline ritual is one command, not three. Run this before handing a
# spec to Kimi/Codex/any executor blind.
#
# It answers: "are this spec's evals well-formed enough to delegate safely?"
#   - structurally valid (validate-task-spec.sh)
#   - eval bodies are shellcheck-clean (no syntax / unquoted-var bugs)
#   - eval bodies EXECUTE without bash errors (broken-logic guard)
#
# For a not-yet-built task the evals are EXPECTED to fail (the work isn't done).
# That is fine — a delegate-safe spec fails for the RIGHT reason (assertion not
# yet true) rather than the WRONG reason (the eval itself is broken bash).
#
# Usage:
#   bash safe-to-delegate.sh <path/to/T-*.md>
#   bash safe-to-delegate.sh --skip-touches-paths <path>   # greenfield create tasks
#   bash safe-to-delegate.sh --require-tier1 <path>         # demand crypto trust
#
# Machine-readable contract (for automated dispatchers):
#   On a clean DELEGATE verdict for a signed-off spec, the gate emits exactly
#   one line of the form `TIER=N` (N = 1|2|3) to stdout. A dispatcher SHOULD
#   parse that line rather than the colored prose:
#     TIER=1  crypto trust (HMAC verified)        -> unsupervised dispatch OK
#     TIER=2  structural-only (no key / no sig)   -> SUPERVISED dispatch ONLY
#     TIER=3  HMAC mismatch                        -> never reached here (hard FAIL)
#   An unsigned spec (no `signed_off: true`) emits no TIER line.
#   With --require-tier1, anything below Tier 1 makes the gate exit 1 — turning
#   the "supervised-only" policy into an enforced control for CI pipelines.
#
# Exit codes:
#   0 — DELEGATE: spec is safe to hand off (Tier 1, or Tier 2 without --require-tier1)
#   1 — DO NOT DELEGATE: structural error, broken eval, shellcheck failure, or
#       (with --require-tier1) a sign-off below Tier 1
#   2 — usage / file error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Source shared lib (TASKSPEC_VERSION, ts_version_flag, ts_die)
# shellcheck source=../lib/_lib.sh
source "$SCRIPT_DIR/../lib/_lib.sh"

# Handle --version uniformly across all task-spec scripts
ts_version_flag "$@"

VALIDATE="$SCRIPT_DIR/validate-task-spec.sh"
RUNNER="$SCRIPT_DIR/run-task-spec.sh"

PASS_THROUGH=()
FILE=""
STAMP=false
STAMP_BY="${USER:-operator}"
REQUIRE_TIER1=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-touches-paths|--skip-id-filename|--skip-depends-on|--skip-exit-coverage)
      PASS_THROUGH+=("$1"); shift ;;
    --stamp)
      STAMP=true; shift ;;
    --stamp-by)
      STAMP=true; STAMP_BY="${2:-operator}"; shift 2 ;;
    --require-tier1)
      REQUIRE_TIER1=true; shift ;;
    --help|-h)
      grep '^#' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)
      echo "Unknown option: $1" >&2; exit 2 ;;
    *)
      if [[ -z "$FILE" ]]; then FILE="$1"; else echo "Too many arguments" >&2; exit 2; fi
      shift ;;
  esac
done

if [[ -z "$FILE" ]]; then
  echo "Usage: safe-to-delegate.sh [--skip-touches-paths] <path/to/T-*.md>" >&2
  exit 2
fi
if [[ ! -f "$FILE" ]]; then
  echo "FAIL: file not found: $FILE" >&2
  exit 2
fi

BOLD=$'\033[1m'; GREEN=$'\033[32m'; RED=$'\033[31m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'
# Disable color when not a TTY
if [[ ! -t 1 ]]; then BOLD=""; GREEN=""; RED=""; YELLOW=""; RESET=""; fi

blockers=0
notes=()

echo "${BOLD}safe-to-delegate: $FILE${RESET}"
echo "────────────────────────────────────────────────────────"

# --- Gate 1: structural + shellcheck validation ---
echo "1. Structural validation + shellcheck-evals ..."
set +e
# bash-3.2 floor: "${PASS_THROUGH[@]}" on an EMPTY array trips `set -u`
# ("unbound variable") on macOS system bash — the `${arr[@]+...}` form is the
# portable empty-safe expansion.
v_out=$(bash "$VALIDATE" --shellcheck-evals ${PASS_THROUGH[@]+"${PASS_THROUGH[@]}"} "$FILE" 2>&1)
v_rc=$?
set -e
if [[ $v_rc -ne 0 ]]; then
  echo "   ${RED}BLOCK${RESET} — validator reported errors:"
  echo "$v_out" | grep -E '^\s+-' | sed 's/^/     /' | head -10
  blockers=$((blockers + 1))
else
  if echo "$v_out" | grep -q '^WARN:'; then
    echo "   ${YELLOW}PASS (with warnings)${RESET}"
    notes+=("validator warnings present — review but not blocking")
  else
    echo "   ${GREEN}PASS${RESET} — structurally valid, shellcheck clean"
  fi
fi

# --- Gate 2: evals execute without bash errors (broken-logic guard) ---
# We run the evals; failures are EXPECTED (work not built). We only block when an
# eval produces a bash-level error (syntax, unbound var, command-not-found),
# which means the eval itself is broken — not the assertion.
echo "2. Eval execution (broken-logic guard) ..."
# The entire analysis runs under set +e: every grep/wc here legitimately returns
# non-zero when it finds nothing, which must NOT abort the gate (CLAUDE.md gotcha).
set +e
r_out=$(bash "$RUNNER" --ci "$FILE" 2>&1)

# Detect bash-level breakage in stderr of any eval: these indicate a BROKEN eval,
# distinct from a clean assertion-fail (which is expected for unbuilt work).
broken=$(printf '%s\n' "$r_out" | grep -oE '"stderr":"[^"]*"' \
  | grep -iE 'syntax error|unbound variable|command not found|unexpected (end|token)|: line [0-9]+:' \
  | head -3)
runner_error=$(printf '%s\n' "$r_out" | grep -oE '"eval":"_runner"[^}]*"status":"fail"[^}]*' | head -1)
passes=$(printf '%s\n' "$r_out" | grep -oE '"status":"pass"' | wc -l | tr -d ' ')
fails=$(printf '%s\n' "$r_out" | grep -oE '"status":"fail"' | wc -l | tr -d ' ')
set -e

if [[ -n "$runner_error" ]]; then
  echo "   ${RED}BLOCK${RESET} — runner could not parse/execute the spec:"
  echo "     $runner_error"
  blockers=$((blockers + 1))
elif [[ -n "$broken" ]]; then
  echo "   ${RED}BLOCK${RESET} — eval body has a bash-level error (broken eval, not a clean fail):"
  echo "$broken" | sed 's/^/     /'
  blockers=$((blockers + 1))
else
  echo "   ${GREEN}PASS${RESET} — evals execute cleanly (${passes:-0} pass / ${fails:-0} fail; fails are expected for unbuilt work)"
  if [[ "${passes:-0}" -gt 0 && "${fails:-0}" -eq 0 ]]; then
    notes+=("ALL evals already pass — task may already be DONE; verify before delegating")
  fi
fi

# --- Verdict ---
echo "────────────────────────────────────────────────────────"
if [[ ${#notes[@]} -gt 0 ]]; then
  for n in "${notes[@]}"; do echo "   ${YELLOW}note:${RESET} $n"; done
fi
if [[ $blockers -eq 0 ]]; then
  echo "${BOLD}${GREEN}VERDICT: DELEGATE${RESET} — safe to hand off blind."
  # TIER is the machine-readable sign-off trust level: 0 = unsigned (no
  # signed_off:true), 1 = crypto trust, 2 = structural-only, 3 = MAC mismatch.
  # It is computed against the spec's ACTUAL on-disk state after any --stamp,
  # then surfaced as a single `TIER=N` line and (with --require-tier1) enforced.
  TIER=0
  # --stamp: the gate writes the autonomy contract into the task frontmatter.
  # This is the Sign-Off Line made real — past this, the task runs unattended.
  if [[ "$STAMP" == true ]]; then
    ts="$(date -u +%FT%TZ)"
    # Write the three envelope fields. CRITICAL: signed_off_by carries a
    # user/CI-controlled value (--stamp-by, $USER). It MUST NOT flow through a
    # sed substitution (a `|` closes the delimiter, an `&` expands to the match)
    # NOR through `awk -v` (which C-escape-expands a backslash-n into a real
    # newline, injecting a forged frontmatter line). ts_set_frontmatter_field is
    # the one serialization path: it carries the value verbatim via the process
    # environment (ENVIRON[]), so every byte — `|`, `&`, `\`, backslash-n, tab —
    # is written literally. The same primitive later writes signed_off_sig.
    if ! ts_set_frontmatter_field "$FILE" "signed_off"    "true" \
       || ! ts_set_frontmatter_field "$FILE" "signed_off_by" "$STAMP_BY" \
       || ! ts_set_frontmatter_field "$FILE" "signed_off_at" "$ts"; then
      echo "   ${RED}BLOCK${RESET} — could not write sign-off envelope (bad --stamp-by value or malformed frontmatter); spec NOT stamped." >&2
      exit 1
    fi
    echo "   ${GREEN}stamped${RESET} signed_off: true by ${STAMP_BY} at ${ts}"

    # --- B2: key-optional HMAC envelope (v2.2) ---
    # The 3 plaintext signed_off* lines are now final on disk. Compute the MAC
    # over the CANONICAL payload (ts_signoff_payload reads those 3 values + the
    # body digest + id, and EXCLUDES the signed_off_sig line itself, so the MAC
    # verifies on the very next read regardless of frontmatter line ordering).
    #
    # Key-optional: with no key (fresh clone / no env var) OR no crypto binary,
    # we DO NOT write a sig and we DO NOT fail — the spec is a structural-only
    # (Tier 2) sign-off, dispatch-eligible for supervised use only. Crypto trust
    # (Tier 1) requires a key + a sha256 provider.
    sig=""
    key="$(ts_resolve_signing_key "$FILE" 2>/dev/null || true)"
    if [[ -n "$key" ]]; then
      set +e
      sig="$(ts_compute_signoff_sig "$FILE" "$key")"
      sig_rc=$?
      set -e
      if [[ $sig_rc -eq 0 && -n "$sig" ]]; then
        # Write the sig via the SAME rewrite-or-inject primitive as the
        # plaintext fields (single serialization path; no sed delimiter).
        if ! ts_set_frontmatter_field "$FILE" "signed_off_sig" "$sig"; then
          echo "   ${RED}BLOCK${RESET} — could not write signed_off_sig into frontmatter; spec stamped but UNSEALED." >&2
          exit 1
        fi
        keyid_disp="${sig#hmac-sha256-v1:}"; keyid_disp="${keyid_disp%%:*}"
        echo "   ${GREEN}sealed${RESET}  signed_off_sig: hmac-sha256-v1 (keyid ${keyid_disp}) — Tier 1 crypto trust"
      else
        echo "   ${YELLOW}note:${RESET} key present but no sha256 provider (openssl/shasum/sha256sum) — structural-only (Tier 2), supervised dispatch only"
      fi
    else
      echo "   ${YELLOW}note:${RESET} no signing key resolved — structural-only (Tier 2), supervised dispatch only. Run configs/setup-taskspec-signing-key.sh or set TASKSPEC_SIGNING_KEY for Tier 1 crypto trust."
    fi
  fi

  # --- Sign-off TIER (computed against actual on-disk state, post-stamp) ---
  # An unsigned spec keeps TIER=0 (no envelope to evaluate). A signed spec is
  # Tier 1 (key+sig present and MAC verifies), Tier 3 (MAC mismatch — should
  # never reach a clean DELEGATE since validate Check 17 hard-fails it), or
  # Tier 2 (structural-only: no key or no sig).
  so_now=$(grep -m1 '^signed_off:' "$FILE" 2>/dev/null | awk -F: '{print $2}' | xargs || true)
  if [[ "${so_now:-}" == "true" ]]; then
    sig_now=$(grep -m1 '^signed_off_sig:' "$FILE" 2>/dev/null | sed -E 's/^signed_off_sig:[[:space:]]*//' || true)
    key_now="$(ts_resolve_signing_key "$FILE" 2>/dev/null || true)"
    if [[ -n "$key_now" && -n "$sig_now" ]]; then
      set +e
      expected_sig="$(ts_compute_signoff_sig "$FILE" "$key_now")"
      set -e
      if [[ -n "$expected_sig" && "$expected_sig" == "$sig_now" ]]; then
        TIER=1
        echo "   ${GREEN}sign-off: Tier 1${RESET} — HMAC verified, full crypto trust (unsupervised dispatch OK)"
      else
        TIER=3
        echo "   ${RED}sign-off: Tier 3${RESET} — HMAC MISMATCH; spec body or envelope modified after stamping (DO NOT DELEGATE unsupervised)"
      fi
    else
      TIER=2
      echo "   ${YELLOW}sign-off: structural-only (Tier 2)${RESET} — supervised dispatch only (no key or no signed_off_sig)"
    fi
  fi

  # Machine-readable tier line for automated dispatchers (parse this, not prose).
  # Emitted only for a signed spec; an unsigned spec has no envelope to report.
  if [[ "${so_now:-}" == "true" ]]; then
    echo "TIER=${TIER}"
  fi

  # --require-tier1: turn the "supervised-only" policy into an ENFORCED control.
  # Anything below Tier 1 (unsigned, structural-only, or a slipped-through
  # mismatch) is a hard FAIL so a CI dispatcher cannot crank it unsupervised.
  if [[ "$REQUIRE_TIER1" == true && "$TIER" != "1" ]]; then
    echo "${BOLD}${RED}VERDICT: DO NOT DELEGATE${RESET} — --require-tier1 set but sign-off is Tier ${TIER} (need Tier 1 crypto trust)." >&2
    exit 1
  fi
  exit 0
else
  echo "${BOLD}${RED}VERDICT: DO NOT DELEGATE${RESET} — $blockers blocker(s) above. Fix the spec first."
  exit 1
fi
