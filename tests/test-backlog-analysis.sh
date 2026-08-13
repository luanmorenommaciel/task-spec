#!/usr/bin/env bash
# Dependency frontier and cross-task backlog analysis contracts.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
READY="$ROOT/src/backlog/list-ready.sh"
LINT="$ROOT/src/backlog/lint-backlog.sh"
WORK="$(mktemp -d -t taskspec-backlog-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/tasks/done"
git -C "$WORK" init -q

write_spec() {
  local path="$1" id="$2" status="$3" effort="$4" deps="$5" touches="$6" creates="$7"
  {
    echo '---'
    printf 'id: %s\ntitle: %s\nstatus: %s\neffort: %s\nagent: any\n' "$id" "$id" "$status" "$effort"
    printf 'depends_on: [%s]\ntouches_paths: [%s]\ncreates_paths: [%s]\n' "$deps" "$touches" "$creates"
    echo 'precondition: (none)'
    echo '---'
    printf '# %s\n' "$id"
  } > "$path"
}

write_spec "$WORK/tasks/done/T-20260811-frontier-a.md" T-20260811-frontier-a done S '' '' ''
write_spec "$WORK/tasks/T-20260811-frontier-b.md" T-20260811-frontier-b ready S 'T-20260811-frontier-a' '' ''
write_spec "$WORK/tasks/T-20260811-frontier-c.md" T-20260811-frontier-c ready S 'T-20260811-missing' '' ''
write_spec "$WORK/tasks/T-20260811-frontier-d.md" T-20260811-frontier-d ready S 'T-20260811-frontier-b' '' ''
write_spec "$WORK/tasks/T-20260811-frontier-node.md" T-20260811-frontier-node ready XL '' '' ''

frontier="$(cd "$WORK" && TASKSPEC_BACKLOG_DIR=tasks bash "$READY")"
all_ready="$(cd "$WORK" && TASKSPEC_BACKLOG_DIR=tasks bash "$READY" --all)"
[[ "$frontier" == *T-20260811-frontier-b* ]]
[[ "$frontier" != *T-20260811-frontier-c* && "$frontier" != *T-20260811-frontier-d* ]]
[[ "$frontier" != *T-20260811-frontier-node* && "$frontier" == *'composition node(s) hidden'* ]]
[[ "$all_ready" == *T-20260811-frontier-b* && "$all_ready" == *T-20260811-frontier-c* && "$all_ready" == *T-20260811-frontier-d* ]]
[[ "$all_ready" != *T-20260811-frontier-node* ]]
echo 'PASS — dependency-aware leaf frontier and --all behavior'

rm -rf "$WORK/tasks"
mkdir -p "$WORK/tasks"
write_spec "$WORK/tasks/T-20260811-lint-one.md" T-20260811-lint-one ready S '' '' 'src/a/file.txt'
write_spec "$WORK/tasks/T-20260811-lint-two.md" T-20260811-lint-two ready S '' '' 'src/b/file.txt'
write_spec "$WORK/tasks/T-20260811-lint-three.md" T-20260811-lint-three ready S '' '' 'src/a/file.txt'
write_spec "$WORK/tasks/T-20260811-lint-dangling.md" T-20260811-lint-dangling ready S 'T-20260811-not-there' '' 'src/c/file.txt'
write_spec "$WORK/tasks/T-20260811-lint-cycle-a.md" T-20260811-lint-cycle-a ready S 'T-20260811-lint-cycle-b' '' 'src/d/file.txt'
write_spec "$WORK/tasks/T-20260811-lint-cycle-b.md" T-20260811-lint-cycle-b ready S 'T-20260811-lint-cycle-a' '' 'src/e/file.txt'

set +e
lint_out="$(cd "$WORK" && TASKSPEC_BACKLOG_DIR=tasks bash "$LINT" 2>&1)"
lint_rc=$?
set -e
[[ "$lint_rc" -eq 1 ]]
[[ "$lint_out" == *"DUAL_CREATE_COLLISION"* ]]
[[ "$lint_out" == *"DANGLING_DEPENDENCY"* ]]
[[ "$lint_out" == *"DEPENDENCY_CYCLE"* ]]
[[ "$lint_out" == *"CONCURRENCY_GROUPS="* ]]
[[ "$lint_out" == *"LINT=ISSUES"* ]]
echo 'PASS — collisions, dangling edges, cycles, and concurrency are reported'

rm -rf "$WORK/tasks"
mkdir -p "$WORK/tasks/archive" "$WORK/tasks/parked"
write_spec "$WORK/tasks/archive/T-20260811-archived-done.md" T-20260811-archived-done done S '' '' ''
write_spec "$WORK/tasks/parked/T-20260811-old-plan.md" T-20260811-old-plan parked S '' '' ''
write_spec "$WORK/tasks/T-20260811-successor.md" T-20260811-successor ready S '' '' ''
sed -i.bak '/^depends_on:/a\
supersedes: T-20260811-old-plan' "$WORK/tasks/T-20260811-successor.md" && rm "$WORK/tasks/T-20260811-successor.md.bak"
write_spec "$WORK/tasks/T-20260811-stale-dependent.md" T-20260811-stale-dependent ready S 'T-20260811-old-plan' '' ''
write_spec "$WORK/tasks/T-20260811-archive-dependent.md" T-20260811-archive-dependent ready S 'T-20260811-archived-done' '' ''
write_spec "$WORK/tasks/T-20260811-blocks-advisory.md" T-20260811-blocks-advisory ready S '' '' ''
sed -i.bak '/^depends_on:/a\
blocks: [T-20260811-not-a-real-dependent]' "$WORK/tasks/T-20260811-blocks-advisory.md" && rm "$WORK/tasks/T-20260811-blocks-advisory.md.bak"

python3 "$ROOT/src/graph/task_graph.py" --backlog "$WORK/tasks" --json > "$WORK/graph-a.json"
python3 "$ROOT/src/graph/task_graph.py" --backlog "$WORK/tasks" --json > "$WORK/graph-b.json"
cmp "$WORK/graph-a.json" "$WORK/graph-b.json"
python3 - "$WORK/graph-a.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert "T-20260811-archive-dependent" in d["ready_frontier"]
assert "T-20260811-successor" in d["ready_frontier"]
assert "T-20260811-stale-dependent" not in d["ready_frontier"]
assert any(x.startswith("stale-superseded:") for x in d["blocked_reasons"]["T-20260811-stale-dependent"])
assert any(x["code"] == "ADVISORY_BLOCKS_MISMATCH" for x in d["issues"])
PY
echo 'PASS — archived dependencies, supersession blocking, advisory blocks, and deterministic graph views'

rm -rf "$WORK/tasks"
mkdir -p "$WORK/tasks/custom/nested"
write_spec "$WORK/tasks/custom/nested/T-20260813-nested.md" T-20260813-nested ready XS '' 'src/shared.txt' ''
write_spec "$WORK/tasks/T-20260813-active.md" T-20260813-active in-progress XS '' 'src/shared.txt' ''
python3 "$ROOT/src/graph/task_graph.py" --backlog "$WORK/tasks" --json > "$WORK/nested-graph.json"
python3 - "$WORK/nested-graph.json" "$ROOT/src/graph" <<'PY'
import json,sys
sys.path.insert(0,sys.argv[2])
from task_graph import active_write_conflicts
view=json.load(open(sys.argv[1]))
assert {node["task_id"] for node in view["nodes"]} == {"T-20260813-nested", "T-20260813-active"}
assert active_write_conflicts(view,"T-20260813-nested")
assert "T-20260813-nested" not in view["ready_frontier"]
assert "write-conflict:T-20260813-active:in-progress" in view["blocked_reasons"]["T-20260813-nested"]
PY
(cd "$WORK" && TASKSPEC_BACKLOG_DIR=tasks bash "$ROOT/src/backlog/transition-status.sh" T-20260813-nested in-progress >/dev/null)
[[ -f "$WORK/tasks/T-20260813-nested.md" ]]
echo 'PASS — recursive task resolution and active write conflicts share one graph universe'

rm -rf "$WORK/tasks"
mkdir -p "$WORK/tasks"
write_spec "$WORK/tasks/T-20260813-leaf-dep.md" T-20260813-leaf-dep done XS '' '' ''
write_spec "$WORK/tasks/T-20260813-parent-dep.md" T-20260813-parent-dep done XS '' '' ''
write_spec "$WORK/tasks/T-20260813-leaf.md" T-20260813-leaf ready XS 'T-20260813-leaf-dep' '' ''
write_spec "$WORK/tasks/T-20260813-parent.md" T-20260813-parent ready XL 'T-20260813-parent-dep' '' ''
write_spec "$WORK/tasks/T-20260813-grandparent.md" T-20260813-grandparent ready XXL '' '' ''
python3 "$ROOT/src/lib/update_frontmatter.py" "$WORK/tasks/T-20260813-parent.md" --set-json '{"children":["T-20260813-leaf"]}'
python3 "$ROOT/src/lib/update_frontmatter.py" "$WORK/tasks/T-20260813-grandparent.md" --set-json '{"children":["T-20260813-parent"]}'
python3 "$ROOT/src/graph/task_graph.py" --backlog "$WORK/tasks" --task T-20260813-leaf --json > "$WORK/closure-graph.json"
python3 - "$WORK/closure-graph.json" <<'PY'
import json,sys
members={item["task_id"] for item in json.load(open(sys.argv[1]))["selected_closure"]["members"]}
assert members == {"T-20260813-leaf", "T-20260813-leaf-dep", "T-20260813-parent", "T-20260813-grandparent"}
assert "T-20260813-parent-dep" not in members
PY
echo 'PASS — dependency closure includes leaf dependencies and composition ancestors only'
