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
[[ "$lint_out" == *"creates_paths collision on 'src/a/file.txt'"* ]]
[[ "$lint_out" == *"depends_on references non-existent task"* ]]
[[ "$lint_out" == *"depends_on cycle detected"* ]]
[[ "$lint_out" == *"concurrency partition"* ]]
[[ "$lint_out" == *"LINT=ISSUES"* ]]
echo 'PASS — collisions, dangling edges, cycles, and concurrency are reported'
