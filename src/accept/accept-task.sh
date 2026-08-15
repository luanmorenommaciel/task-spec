#!/usr/bin/env bash
# accept-task.sh — independent POST-gate with revision, attempt, graph, Git, and evidence binding.
#
# Usage:
#   taskspec accept [--stamp] [--handoff FILE] [--gold-sanity]
#     [--no-blast-radius] [--allow-tier2 --supervised-by ID --reason TEXT]
#     [receipt and trust flags] <task-spec>
#
# Exit: 0 accepted; 1 contract/eval/policy rejection; 2 usage.
set -euo pipefail

# In global JSON mode, keep the human gate trace on stderr and reserve stdout
# for the single structured acceptance result consumed by the CLI envelope.
# fd 3 always points at the caller's original stdout.
exec 3>&1
if [[ "${TASKSPEC_JSON_MODE:-0}" == "1" ]]; then
  exec 1>&2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/_lib.sh
source "$SCRIPT_DIR/../lib/_lib.sh"
ts_version_flag "$@"

FILE=""; HANDOFF=""; STAMP=false; CHECK_BLAST=true; GOLD_SANITY=false
ACCEPTED_BY="${USER:-operator}"; ALLOW_TIER2=false; SUPERVISED_BY=""; TIER2_REASON=""
BASE_REF=""; HOLDOUT_RECEIPT=""; GRADED_RECEIPT=""; HUMAN_RECEIPT=""
ENVIRONMENT_RECEIPT=""; IDENTITY_RECEIPT=""; IDENTITY_PUBLIC_KEY=""
IDENTITY_REVOCATIONS=""; TRUST_REGISTRY=""; ACCEPTANCE_DIR=""; VERIFIER_SIGNATURE=""

need_value() { [[ $# -ge 2 && -n "${2:-}" ]] || { echo "taskspec accept: $1 requires a value" >&2; exit 2; }; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stamp) STAMP=true; shift ;;
    --handoff) need_value "$@"; HANDOFF="$2"; shift 2 ;;
    --no-blast-radius) CHECK_BLAST=false; shift ;;
    --gold-sanity) GOLD_SANITY=true; shift ;;
    --accepted-by) need_value "$@"; ACCEPTED_BY="$2"; shift 2 ;;
    --base) need_value "$@"; BASE_REF="$2"; shift 2 ;;
    --allow-tier2) ALLOW_TIER2=true; shift ;;
    --supervised-by) need_value "$@"; SUPERVISED_BY="$2"; shift 2 ;;
    --reason) need_value "$@"; TIER2_REASON="$2"; shift 2 ;;
    --holdout-receipt) need_value "$@"; HOLDOUT_RECEIPT="$2"; shift 2 ;;
    --graded-receipt) need_value "$@"; GRADED_RECEIPT="$2"; shift 2 ;;
    --human-receipt) need_value "$@"; HUMAN_RECEIPT="$2"; shift 2 ;;
    --environment-receipt) need_value "$@"; ENVIRONMENT_RECEIPT="$2"; shift 2 ;;
    --identity-receipt) need_value "$@"; IDENTITY_RECEIPT="$2"; shift 2 ;;
    --identity-public-key) need_value "$@"; IDENTITY_PUBLIC_KEY="$2"; shift 2 ;;
    --identity-revocations) need_value "$@"; IDENTITY_REVOCATIONS="$2"; shift 2 ;;
    --trust-registry) need_value "$@"; TRUST_REGISTRY="$2"; shift 2 ;;
    --acceptance-dir) need_value "$@"; ACCEPTANCE_DIR="$2"; shift 2 ;;
    --verifier-signature) need_value "$@"; VERIFIER_SIGNATURE="$2"; shift 2 ;;
    --help|-h) grep '^#' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "taskspec accept: unknown option: $1" >&2; exit 2 ;;
    *) if [[ -z "$FILE" ]]; then FILE="$1"; else echo "taskspec accept: too many arguments" >&2; exit 2; fi; shift ;;
  esac
done
[[ -n "$FILE" ]] || { echo "Usage: taskspec accept [options] <task-spec>" >&2; exit 2; }
[[ -f "$FILE" ]] || { echo "taskspec accept: file not found: $FILE" >&2; exit 2; }
[[ -z "$HANDOFF" || -f "$HANDOFF" ]] || { echo "taskspec accept: handoff not found: $HANDOFF" >&2; exit 2; }

BOLD=$'\033[1m'; GREEN=$'\033[32m'; RED=$'\033[31m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'
if ! ts_color_enabled; then BOLD=""; GREEN=""; RED=""; YELLOW=""; RESET=""; fi
tmp_dir="$(mktemp -d -t taskspec-accept-XXXXXX)"
trap 'rm -rf "$tmp_dir"' EXIT
blockers=0; tier=1; failure_code=""; tier2_reasons=()
fail_gate() { blockers=$((blockers + 1)); [[ -n "$failure_code" ]] || failure_code="$1"; echo "   ${RED}BLOCK${RESET} [$1] — $2"; }
downgrade() { tier=2; tier2_reasons+=("$1"); }

echo "${BOLD}accept-task: $FILE${RESET}"
echo "────────────────────────────────────────────────────────"

SO="$(grep -m1 '^signed_off:' "$FILE" 2>/dev/null | awk -F: '{print $2}' | xargs || true)"
[[ "$SO" == "true" ]] || fail_gate POLICY_TAMPER "spec is not signed_off:true"

echo "A. Independent evaluation ..."
set +e
a_out="$(bash "$SCRIPT_DIR/../gate/run-task-spec.sh" "$FILE" 2>&1)"; a_rc=$?
set -e
if [[ $a_rc -eq 0 ]]; then echo "   ${GREEN}PASS${RESET} — Exit Check returned 0"
else fail_gate EVAL_FAILED "Exit Check failed (rc=$a_rc)"; printf '%s\n' "$a_out" | tail -8 | sed 's/^/     /'; fi

echo "B. Handoff, graph, base commit, and blast radius ..."
preflight_args=("$FILE" --json)
[[ -n "$HANDOFF" ]] && preflight_args+=(--handoff "$HANDOFF")
[[ "$CHECK_BLAST" == false ]] && preflight_args+=(--no-blast-radius)
for receipt in "$HOLDOUT_RECEIPT" "$GRADED_RECEIPT" "$HUMAN_RECEIPT" "$ENVIRONMENT_RECEIPT" "$IDENTITY_RECEIPT" "$IDENTITY_PUBLIC_KEY" "$IDENTITY_REVOCATIONS" "$TRUST_REGISTRY"; do
  [[ -n "$receipt" ]] && preflight_args+=(--bookkeeping "$receipt")
done
set +e
python3 "$SCRIPT_DIR/preflight.py" ${preflight_args[@]+"${preflight_args[@]}"} >"$tmp_dir/preflight.json"
preflight_rc=$?
set -e
if [[ $preflight_rc -eq 0 ]]; then
  echo "   ${GREEN}PASS${RESET} — revision, closure, Git base, and write scope agree"
else
  while IFS=$'\t' read -r code message; do fail_gate "$code" "$message"; done < <(
    python3 - "$tmp_dir/preflight.json" <<'PY'
import json,sys
for e in json.load(open(sys.argv[1]))["errors"]: print(e["code"], e["message"], sep="\t")
PY
  )
fi
while IFS= read -r reason; do [[ -n "$reason" ]] && downgrade "$reason"; done < <(
  python3 - "$tmp_dir/preflight.json" <<'PY'
import json,sys
for value in json.load(open(sys.argv[1])).get("tier2_reasons",[]): print(value)
PY
)

echo "C. Authorization integrity ..."
SIGNED_SIG="$(grep -m1 '^signed_off_sig:' "$FILE" 2>/dev/null | sed -E 's/^signed_off_sig:[[:space:]]*//' || true)"
scheme="${SIGNED_SIG%%:*}"
case "$scheme" in
  hmac-sha256-v3) sig_version=v3 ;;
  hmac-sha256-v2) sig_version=v2; downgrade AUTHENTIC_BUT_NARROW_V2 ;;
  hmac-sha256-v1) sig_version=v1; downgrade AUTHENTIC_BUT_NARROW_V1 ;;
  *) sig_version=""; downgrade AUTHORIZATION_UNVERIFIED ;;
esac
set +e
SIGN_KEY="$(ts_resolve_signing_key "$FILE" 2>/dev/null)"
set -e
if [[ -z "$SIGN_KEY" || -z "$sig_version" ]]; then
  echo "   ${YELLOW}Tier 2${RESET} — authorization cannot be cryptographically verified"
  downgrade AUTHORIZATION_KEY_UNAVAILABLE
else
  set +e
  EXPECTED_SIG="$(ts_compute_signoff_sig "$FILE" "$SIGN_KEY" "$sig_version")"; sig_rc=$?
  set -e
  if [[ $sig_rc -ne 0 ]]; then downgrade AUTHORIZATION_CRYPTO_UNAVAILABLE; echo "   ${YELLOW}Tier 2${RESET} — crypto provider unavailable"
  elif [[ "$EXPECTED_SIG" != "$SIGNED_SIG" ]]; then fail_gate POLICY_TAMPER "authorization HMAC mismatch"
  elif [[ "$scheme" == "hmac-sha256-v3" ]]; then echo "   ${GREEN}PASS${RESET} — TaskAuthorization/v3 verifies"
  else echo "   ${YELLOW}Tier 2${RESET} — historical authorization verifies on narrower terms"; fi
fi

if [[ "$GOLD_SANITY" == true ]]; then
  echo "D. Gold-sanity ..."
  if [[ -z "$BASE_REF" && -n "$HANDOFF" ]]; then
    BASE_REF="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source"]["base_commit"])' "$HANDOFF" 2>/dev/null || true)"
  fi
  [[ -n "$BASE_REF" ]] || BASE_REF=HEAD
  set +e
  python3 "$SCRIPT_DIR/../evidence/eval_audit.py" "$FILE" --baseline "$BASE_REF" --report "$tmp_dir/eval-audit.json" >/dev/null 2>&1
  gold_rc=$?
  set -e
  if [[ $gold_rc -eq 0 ]]; then echo "   ${GREEN}PASS${RESET} — eval discriminates baseline from current work"
  else fail_gate EVAL_NONDISCRIMINATING "eval did not prove baseline discrimination"; fi
fi

echo "E. Sealed evidence policy ..."
policy_args=("$FILE" --json)
[[ -n "$HANDOFF" ]] && policy_args+=(--handoff "$HANDOFF")
[[ -n "$HOLDOUT_RECEIPT" ]] && policy_args+=(--holdout-receipt "$HOLDOUT_RECEIPT")
[[ -n "$GRADED_RECEIPT" ]] && policy_args+=(--graded-receipt "$GRADED_RECEIPT")
[[ -n "$HUMAN_RECEIPT" ]] && policy_args+=(--human-receipt "$HUMAN_RECEIPT")
[[ -n "$ENVIRONMENT_RECEIPT" ]] && policy_args+=(--environment-receipt "$ENVIRONMENT_RECEIPT")
[[ -n "$IDENTITY_RECEIPT" ]] && policy_args+=(--identity-receipt "$IDENTITY_RECEIPT")
[[ -n "$IDENTITY_PUBLIC_KEY" ]] && policy_args+=(--identity-public-key "$IDENTITY_PUBLIC_KEY")
[[ -n "$IDENTITY_REVOCATIONS" ]] && policy_args+=(--identity-revocations "$IDENTITY_REVOCATIONS")
[[ -n "$TRUST_REGISTRY" ]] && policy_args+=(--trust-registry "$TRUST_REGISTRY")
set +e
python3 "$SCRIPT_DIR/../evidence/post_policy.py" ${policy_args[@]+"${policy_args[@]}"} >"$tmp_dir/policy.json"
policy_rc=$?
set -e
if [[ $policy_rc -eq 0 ]]; then echo "   ${GREEN}PASS${RESET} — required evidence matches this attempt"
else
  code="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print((d.get("failure_codes") or ["RECEIPT_MISSING"])[0])' "$tmp_dir/policy.json")"
  message="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("; ".join(d.get("errors",[])))' "$tmp_dir/policy.json")"
  fail_gate "$code" "$message"
fi
policy_tier="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("tier",1))' "$tmp_dir/policy.json")"
[[ "$policy_tier" == "2" ]] && downgrade LEGACY_RECEIPT

if [[ $tier -eq 2 ]]; then
  if [[ "$ALLOW_TIER2" != true || -z "$SUPERVISED_BY" || -z "$TIER2_REASON" ]]; then
    fail_gate TIER_TOO_LOW "Tier-2 acceptance requires --allow-tier2 --supervised-by <identity> --reason <text>"
  else
    echo "   ${YELLOW}Tier 2 supervised${RESET} — ${tier2_reasons[*]}"
  fi
fi

echo "────────────────────────────────────────────────────────"
if [[ $blockers -ne 0 ]]; then
  echo "${BOLD}${RED}VERDICT: REJECT${RESET} — $blockers gate(s) failed"
  echo "ACCEPTANCE_FAILURE=${failure_code:-TIER_TOO_LOW}"
  echo "ACCEPTED=0"
  exit 1
fi

if [[ "$STAMP" == true ]]; then
  finalize_args=("$FILE" --preflight "$tmp_dir/preflight.json" --policy "$tmp_dir/policy.json" --accepted-by "$ACCEPTED_BY" --tier "$tier")
  [[ -n "$HANDOFF" ]] && finalize_args+=(--handoff "$HANDOFF")
  [[ -n "$SUPERVISED_BY" ]] && finalize_args+=(--supervised-by "$SUPERVISED_BY")
  [[ -n "$TIER2_REASON" ]] && finalize_args+=(--reason "$TIER2_REASON")
  [[ -n "$ACCEPTANCE_DIR" ]] && finalize_args+=(--acceptance-dir "$ACCEPTANCE_DIR")
  [[ -n "$VERIFIER_SIGNATURE" ]] && finalize_args+=(--verifier-signature "$VERIFIER_SIGNATURE")
  for receipt in "$HOLDOUT_RECEIPT" "$GRADED_RECEIPT" "$HUMAN_RECEIPT" "$ENVIRONMENT_RECEIPT" "$IDENTITY_RECEIPT"; do
    [[ -n "$receipt" ]] && finalize_args+=(--receipt "$receipt")
  done
  set +e
  finalize_out="$(python3 "$SCRIPT_DIR/finalize.py" ${finalize_args[@]+"${finalize_args[@]}"} 2>&1)"; finalize_rc=$?
  set -e
  if [[ $finalize_rc -ne 0 ]]; then fail_gate POLICY_TAMPER "$finalize_out"; echo "ACCEPTED=0"; exit 1; fi
  echo "   ${GREEN}stamped${RESET} — $finalize_out"
fi
echo "${BOLD}${GREEN}VERDICT: ACCEPT${RESET} — Tier $tier evidence is bound to the authorized task attempt"
echo "ACCEPTED=1"
if [[ "${TASKSPEC_JSON_MODE:-0}" == "1" ]]; then
  if [[ "$STAMP" == true ]]; then
    printf '%s\n' "$finalize_out" >&3
  else
    printf '{"contract":"AcceptanceResult/v1","accepted":true,"tier":%s}\n' "$tier" >&3
  fi
fi
