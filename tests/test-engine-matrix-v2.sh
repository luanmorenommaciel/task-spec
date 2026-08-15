#!/usr/bin/env bash
# Deterministic EngineMatrix/v2 proof with fake secret-free Codex and Claude adapters.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d -t taskspec-engine-v2-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
MATRIX_ROOT="$WORK/evidence/3.8.1"
KEY="$WORK/evaluator-signing-key"
mkdir -p "$MATRIX_ROOT/benchmark" "$WORK/bin" "$WORK/out"
cp -R "$ROOT/evidence/3.8.1/benchmark/snapshots" "$MATRIX_ROOT/benchmark/snapshots"
printf '%s\n' 'fixture-only-engine-matrix-key' > "$KEY"
chmod 600 "$KEY"

seal_snapshot() {
  local case_name="$1" stamp_root="$WORK/stamp/$1" spec
  mkdir -p "$stamp_root"
  cp -R "$MATRIX_ROOT/benchmark/snapshots/$case_name/." "$stamp_root/"
  spec="$(find "$stamp_root/tasks" -name '*.md' -type f)"
  sed -i.bak \
    -e 's/^signed_off: true$/signed_off: false/' \
    -e 's/^signed_off_by: .*$/signed_off_by: (none)/' \
    -e 's/^signed_off_at: .*$/signed_off_at: (none)/' \
    -e 's/^signed_off_sig: .*$/signed_off_sig: (none)/' "$spec"
  rm "$spec.bak"
  git -C "$stamp_root" init -q
  git -C "$stamp_root" config user.name "Task-Spec Matrix Test"
  git -C "$stamp_root" config user.email "matrix@taskspec.invalid"
  git -C "$stamp_root" add .
  git -C "$stamp_root" commit -q -m fixture
  TASKSPEC_SIGNING_KEY="$KEY" TASKSPEC_WORKSPACE_ROOT="$stamp_root" \
    "$ROOT/bin/taskspec" gate --stamp --stamp-by matrix-test "$spec" >/dev/null
  cp "$spec" "$MATRIX_ROOT/benchmark/snapshots/$case_name/tasks/"
}

for case_name in xs s m; do seal_snapshot "$case_name"; done

mkdir -p "$MATRIX_ROOT/benchmark/handoffs"
build_handoff() {
  local case_name="$1" attempt="$2" case_root seed bare worktree spec retained_spec
  case_root="/tmp/taskspec-3.8.1-engine-matrix/$case_name"
  rm -rf "$case_root"
  seed="$case_root/seed"
  bare="$case_root/repo.git"
  worktree="$case_root/worktree"
  mkdir -p "$seed"
  cp -R "$MATRIX_ROOT/benchmark/snapshots/$case_name/." "$seed/"
  spec="$(find "$seed/tasks" -name '*.md' -type f)"
  retained_spec="$(find "$MATRIX_ROOT/benchmark/snapshots/$case_name/tasks" -name '*.md' -type f)"
  sed -i.bak \
    -e 's/^signed_off: true$/signed_off: false/' \
    -e 's/^signed_off_by: .*$/signed_off_by: (none)/' \
    -e 's/^signed_off_at: .*$/signed_off_at: (none)/' \
    -e 's/^signed_off_sig: .*$/signed_off_sig: (none)/' "$spec"
  rm "$spec.bak"
  git -C "$seed" init -q
  git -C "$seed" config user.name "Task-Spec Benchmark"
  git -C "$seed" config user.email "benchmark@taskspec.invalid"
  git -C "$seed" add .
  GIT_AUTHOR_DATE=2026-08-15T00:00:00Z GIT_COMMITTER_DATE=2026-08-15T00:00:00Z \
    git -C "$seed" commit -q -m "frozen benchmark snapshot"
  cp "$retained_spec" "$seed/tasks/"
  git -C "$seed" add tasks
  GIT_AUTHOR_DATE=2026-08-15T00:01:00Z GIT_COMMITTER_DATE=2026-08-15T00:01:00Z \
    git -C "$seed" commit -q -m "seal benchmark task"
  git clone -q --bare "$seed" "$bare"
  git --git-dir="$bare" worktree add -q --detach "$worktree" HEAD
  spec="$(find "$worktree/tasks" -name '*.md' -type f)"
  TASKSPEC_SIGNING_KEY="$KEY" TASKSPEC_WORKSPACE_ROOT="$worktree" \
    "$ROOT/bin/taskspec" handoff "$spec" --backend any --attempt-id "$attempt" \
      --out "$MATRIX_ROOT/benchmark/handoffs/$case_name.json" >/dev/null
}

build_handoff xs 38100000-0000-4000-8000-000000000001
build_handoff s 38100000-0000-4000-8000-000000000002
build_handoff m 38100000-0000-4000-8000-000000000003

python3 - "$MATRIX_ROOT" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
tasks = []
for effort in ("XS", "S", "M"):
    handoff = root / "benchmark" / "handoffs" / f"{effort.lower()}.json"
    value = json.loads(handoff.read_text())
    tasks.append({
        "task_id": value["task_id"], "effort": effort,
        "handoff": f"benchmark/handoffs/{effort.lower()}.json",
        "handoff_digest": "sha256:" + hashlib.sha256(handoff.read_bytes()).hexdigest(),
    })
matrix = {
    "contract": "EngineMatrix/v2", "matrix_id": "taskspec-3.8.1-test",
    "frozen_at": "2026-08-15T19:07:00Z", "tasks": tasks,
    "engines": [
        {"family": "openai", "adapter": "codex", "model": "gpt-5.6-sol", "enabled": True,
         "max_attempts": 1, "budget": {"timeout_sec": 60, "max_cost_usd": None}},
        {"family": "anthropic", "adapter": "claude", "model": "opus", "enabled": True,
         "max_attempts": 1, "budget": {"timeout_sec": 60, "max_cost_usd": 1}},
    ],
}
(root / "engine-matrix.json").write_text(json.dumps(matrix, indent=2) + "\n")
PY

cat > "$WORK/bin/fake-engine" <<'PY'
#!/usr/bin/env python3
import json, os, pathlib, subprocess, sys
name = pathlib.Path(sys.argv[0]).name
if "--version" in sys.argv:
    print("codex-cli fixture" if name == "codex" else "2.1.233 fixture")
    raise SystemExit(0)
if any(key.startswith("TASKSPEC_") or "API_KEY" in key.upper() for key in os.environ):
    raise SystemExit(77)
common = subprocess.check_output(["git", "rev-parse", "--git-common-dir"], text=True).strip()
if (pathlib.Path(common) / "info" / "taskspec-signing-key").exists():
    raise SystemExit(78)
prompt = sys.stdin.read()
assert "TaskHandoff/v3" in prompt
cwd = pathlib.Path.cwd()
if cwd.parent.name == "xs":
    target = cwd / "work/xs/result.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("task-spec-xs-ok\n")
elif cwd.parent.name == "s":
    (cwd / "work/s/search_cli.py").write_text('''#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("query"); parser.add_argument("--json", action="store_true")
    args=parser.parse_args(); matches=[{"path":"docs/task-spec.md","score":1}] if args.query == "task" else []
    if args.json: print(json.dumps({"query":args.query,"results":matches}, sort_keys=True))
    elif matches:
        print("PATH\\tSCORE")
        for match in matches: print("{}\\t{}".format(match["path"], match["score"]))
    else: print("No results for: {}".format(args.query))
    return 0
if __name__ == "__main__": raise SystemExit(main())
''')
else:
    (cwd / "work/m/task_graph.py").write_text('''#!/usr/bin/env python3
from __future__ import annotations
def ready(tasks):
    memo={}
    def satisfied(task_id, visiting=()):
        if task_id in memo: return memo[task_id]
        if task_id in visiting: return False
        task=tasks[task_id]
        value=task["status"] == "done" and all(satisfied(dep, visiting+(task_id,)) for dep in task.get("depends_on", []))
        memo[task_id]=value; return value
    return sorted(task_id for task_id, task in tasks.items() if task["status"] == "pending" and all(satisfied(dep) for dep in task.get("depends_on", [])))
def assert_acyclic(tasks):
    visited=set(); active=[]
    def visit(node):
        if node in active:
            cycle=active[active.index(node):]+[node]
            raise ValueError("cycle: " + " -> ".join(cycle))
        if node in visited: return
        active.append(node)
        for dep in tasks[node].get("depends_on", []): visit(dep)
        active.pop(); visited.add(node)
    for node in sorted(tasks): visit(node)
''')
if name == "codex":
    print(json.dumps({"type":"turn.completed","model":"gpt-5.6-sol","usage":{"input_tokens":1,"output_tokens":1}}))
else:
    print(json.dumps({"type":"system","model":"claude-opus-fixture"}))
    print(json.dumps({"type":"result","total_cost_usd":0.01,"usage":{"input_tokens":1,"output_tokens":1}}))
PY
chmod +x "$WORK/bin/fake-engine"
ln -s "$WORK/bin/fake-engine" "$WORK/bin/codex"
ln -s "$WORK/bin/fake-engine" "$WORK/bin/claude"

PATH="$WORK/bin:$PATH" TASKSPEC_EVIDENCE_SIGNING_KEY="$KEY" \
  python3 "$ROOT/src/evidence/engine_matrix.py" validate "$MATRIX_ROOT/engine-matrix.json" \
  | grep -q 'contract=EngineMatrix/v2'
PATH="$WORK/bin:$PATH" TASKSPEC_EVIDENCE_SIGNING_KEY="$KEY" \
  python3 "$ROOT/src/evidence/engine_matrix.py" run "$MATRIX_ROOT/engine-matrix.json" \
    --out-dir "$WORK/out" --result "$WORK/result.json" --artifacts "$WORK/artifacts.json" >/dev/null

python3 - "$WORK/result.json" "$WORK/artifacts.json" <<'PY'
import json, sys
result = json.load(open(sys.argv[1]))
artifacts = json.load(open(sys.argv[2]))
assert result["contract"] == "EngineMatrixResult/v2"
assert result["summary"] == {"required_families": 2, "families_passing": 2, "scope_violations": 0, "passed": True}
assert [row["family"] for row in result["results"]] == ["openai", "anthropic"]
assert all(row["state"] == "pass" and row["accepted_count"] == 3 for row in result["results"])
assert all(len(row["attempts"]) == 3 for row in result["results"])
assert all(attempt["status"] == "accepted" and not attempt["scope_violation"] for row in result["results"] for attempt in row["attempts"])
assert artifacts["raw_artifacts_committed"] is False and len(artifacts["attempts"]) == 6
assert all(not row["environment"]["credential_values_retained"] for row in artifacts["attempts"])
assert all("SSH_AUTH_SOCK" in row["environment"]["removed_variable_names"] or "SSH_AUTH_SOCK" not in row["environment"]["inherited_variable_names"] for row in artifacts["attempts"])
PY

python3 - "$MATRIX_ROOT/engine-matrix.json" "$WORK/tampered.json" <<'PY'
import json, sys
value=json.load(open(sys.argv[1])); value["tasks"][0]["handoff_digest"]="sha256:"+"0"*64
json.dump(value, open(sys.argv[2], "w"), indent=2)
PY
if python3 "$ROOT/src/evidence/engine_matrix.py" validate "$WORK/tampered.json" >/dev/null 2>&1; then
  echo "tampered matrix unexpectedly validated" >&2
  exit 1
fi

echo "ENGINE_MATRIX_V2=READY"
