#!/usr/bin/env bash
# Installed canonical example and reviewer-grade 3.8.1 documentation contract.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d -t taskspec-v381-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
TARGET="$WORK/project"
INSTALL_ROOT="$WORK/install-root"
BIN_DIR="$WORK/bin"
mkdir -p "$TARGET" "$INSTALL_ROOT" "$BIN_DIR"

TASKSPEC_INSTALL_ROOT="$INSTALL_ROOT" bash "$ROOT/install.sh" \
  --target "$TARGET" --copy --bin-dir "$BIN_DIR" >"$WORK/install.out"
grep -q '^INSTALL=OK$' "$WORK/install.out"
TS="$BIN_DIR/taskspec"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
[[ "$($TS version)" == "$VERSION" ]]

"$TS" help example >"$WORK/help.out"
grep -q '^Usage: taskspec example task-plan --out <file> \[--force\]$' "$WORK/help.out"
for shell_name in bash zsh fish; do
  "$TS" completion "$shell_name" >"$WORK/completion-$shell_name.out"
  grep -q 'example' "$WORK/completion-$shell_name.out"
done
"$TS" agent-context >"$WORK/agent-context.json"
python3 - "$WORK/agent-context.json" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
contract = value["commands"]["example"]
assert contract["tokens"] == ["EXAMPLE=WRITTEN", "EXAMPLE=DRY_RUN", "EXAMPLE=REFUSED"]
assert "non-clobberingly" in contract["mutation"]
PY

(
  cd "$TARGET"
  "$TS" example task-plan --out tasks/.plans/reviewer.yaml >"$WORK/write.out"
  grep -q '^EXAMPLE=WRITTEN ' "$WORK/write.out"
  cmp "$INSTALL_ROOT/$VERSION/docs/examples/task-plan.yaml" tasks/.plans/reviewer.yaml
  "$TS" plan --manifest tasks/.plans/reviewer.yaml >"$WORK/plan.out"
  grep -q '^TASK_PLAN=OK$' "$WORK/plan.out"

  cp tasks/.plans/reviewer.yaml "$WORK/original.yaml"
  set +e
  "$TS" example task-plan --out tasks/.plans/reviewer.yaml >"$WORK/refused.out" 2>&1
  refused_rc=$?
  set -e
  [[ "$refused_rc" -eq 1 ]]
  grep -q '^EXAMPLE=REFUSED ' "$WORK/refused.out"
  cmp "$WORK/original.yaml" tasks/.plans/reviewer.yaml

  printf 'stale\n' > tasks/.plans/reviewer.yaml
  "$TS" example task-plan --out tasks/.plans/reviewer.yaml --force >"$WORK/force.out"
  grep -q 'action=replaced' "$WORK/force.out"
  cmp "$INSTALL_ROOT/$VERSION/docs/examples/task-plan.yaml" tasks/.plans/reviewer.yaml

  "$TS" --json example task-plan --out tasks/.plans/json.yaml >"$WORK/example.json"
  python3 - "$WORK/example.json" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["contract"] == "TaskSpecCLIResult/v1"
assert value["command"] == "example" and value["ok"] is True and value["exit_code"] == 0
data = value["data"]
assert data["contract"] == "TaskSpecExampleResult/v1"
assert data["written"] is True and data["created"] is True and data["overwritten"] is False
assert data["digest"].startswith("sha256:") and value["stdout"] == ""
PY

  "$TS" --json --dry-run example task-plan --out tasks/.plans/dry-run.yaml >"$WORK/dry-run.json"
  [[ ! -e tasks/.plans/dry-run.yaml ]]
  python3 - "$WORK/dry-run.json" <<'PY'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
data = value["data"]
assert value["ok"] is True and data["dry_run"] is True
assert data["written"] is False and data["created"] is False and data["overwritten"] is False
PY
)

python3 "$ROOT/tests/readme_contract.py" >"$WORK/readme.out"
grep -q '^README_COMMANDS=READY ' "$WORK/readme.out"
python3 "$ROOT/tools/render-cli-reference.py" --check "$ROOT/docs/reference/cli.md"
python3 "$ROOT/src/evidence/release_audit.py" check
python3 "$ROOT/tools/render-status.py" --check "$ROOT/README.md"
python3 - "$ROOT" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
report = json.loads((root / "release/3.8.1/reviewer-report.json").read_text(encoding="utf-8"))
assert report["contract"] == "TaskSpecReviewerReport/v1" and report["result"] == "pass"
assert {check["id"] for check in report["checks"]} >= {
    "installed-example", "cli-discovery", "documentation-contract",
    "viewport-390", "viewport-1440", "truth-boundaries",
}
assert all(check["state"] == "pass" for check in report["checks"])
# These are retained 3.8.1 observations, not a claim that evolving 3.9 source
# files remain byte-identical. Their enclosing report digest is pinned by
# release/evidence.json; current documentation is checked independently above.
for artifact in report["artifacts"]:
    assert artifact["path"] and artifact["digest"].startswith("sha256:")
PY

grep -q 'taskspec example task-plan --out tasks/.plans/reviewer.yaml' \
  "$ROOT/docs/getting-started/reviewer-route.md"
(cd "$ROOT" && make release-audit >"$WORK/release-audit.out" 2>&1) || true
grep -q '^PROTOCOLS=READY$' "$WORK/release-audit.out"

echo "V381_EXPERIENCE=READY"
