#!/usr/bin/env bash
# lint-docs.sh — markdown hygiene lint for the repo's documentation surface.
#
# Checks, over the curated doc set (README, AGENTS, docs/, harness/, spec/
#   — NOT tests/fixtures or src/templates, which
# deliberately contain broken/{{TODO}} content):
#   1. Local relative links/images resolve to existing files (anchors stripped).
#   2. Code fences are balanced (every ``` opens and closes).
#
# bash-3.2 safe. Exit 0 clean, exit 1 with a report otherwise.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

failures=0

report() {
  printf 'lint-docs: FAIL %s\n' "$1" >&2
  failures=$((failures + 1))
}

# Collect the doc set (portable; no mapfile).
doc_files() {
  printf '%s\n' README.md AGENTS.md
  find docs harness spec -name '*.md' -type f ! -path '*/node_modules/*' 2>/dev/null
}

check_links() {
  local file="$1"
  local dir
  dir="$(dirname "$file")"
  # Extract markdown link/image targets and HTML src/href attributes.
  # `|| true`: grep exits 1 on files with no links; pipefail would kill us.
  { grep -oE '\]\([^)]+\)|src="[^"]+"|href="[^"]+"' "$file" 2>/dev/null || true; } | while IFS= read -r raw; do
    local target
    target="$raw"
    target="${target#](}" ; target="${target%)}"
    target="${target#src=\"}" ; target="${target#href=\"}" ; target="${target%\"}"
    # Skip external, anchor-only, and mailto links.
    case "$target" in
      http://*|https://*|mailto:*|\#*|'') continue ;;
    esac
    # Strip title ("path "title"") and anchor.
    target="${target%% *}"
    target="${target%%#*}"
    [ -z "$target" ] && continue
    # URL-decoded spaces.
    target="${target//%20/ }"
    if [ ! -e "$dir/$target" ] && [ ! -e "$target" ]; then
      printf 'BROKEN\t%s\t%s\n' "$file" "$target"
    fi
  done
}

check_fences() {
  local file="$1"
  local n
  n=$(grep -c '^```' "$file" 2>/dev/null || true)
  n="${n:-0}"
  if [ $((n % 2)) -ne 0 ]; then
    printf 'FENCE\t%s\t%s fence lines (odd)\n' "$file" "$n"
  fi
}

report_file="$(mktemp "${TMPDIR:-/tmp}/lint-docs-report.XXXXXX")"
trap 'rm -f "$report_file"' EXIT

while IFS= read -r f; do
  [ -f "$f" ] || continue
  check_links "$f"
  check_fences "$f"
done < <(doc_files) | sort -u > "$report_file"

if [ -s "$report_file" ]; then
  while IFS=$'\t' read -r kind file target; do
    case "$kind" in
      BROKEN) report "$file -> $target (no such file)" ;;
      FENCE)  report "$file: unbalanced code fences ($target)" ;;
    esac
  done < "$report_file"
fi

if [ "$failures" -gt 0 ]; then
  printf 'lint-docs: %d failure(s)\n' "$failures" >&2
  exit 1
fi
python3 tools/render-cli-reference.py --check docs/reference/cli.md
printf 'lint-docs: OK\n'
