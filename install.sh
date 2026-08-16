#!/usr/bin/env bash
# Install a pinned Task-Spec engine, CLI launcher, and equivalent harness skills.
set -euo pipefail

PINNED_VERSION="3.8.1"
REPOSITORY="luanmorenommaciel/task-spec"
TARGET="$PWD"
MODE="copy"
BIN_DIR="${HOME}/.local/bin"
NO_BIN=false
FORCE=false

usage() {
  cat <<'EOF'
Usage: install.sh [options]
  --global           install user-level skills for Codex/Kimi, Claude, and Grok
  --target DIR       repository receiving harness skills (default: PWD)
  --copy             pinned copy installation (default)
  --symlink          checkout-development mode; source must be a local checkout
  --bin-dir DIR      CLI launcher directory (default: ~/.local/bin)
  --no-bin           install skills only
  --force            back up and replace existing managed destinations
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global)
      [[ -n "${HOME:-}" ]] || { echo "install.sh: HOME is required for --global" >&2; exit 2; }
      TARGET="$HOME"
      shift
      ;;
    --target) TARGET="${2:-}"; shift 2 ;;
    --target=*) TARGET="${1#*=}"; shift ;;
    --copy) MODE="copy"; shift ;;
    --symlink) MODE="symlink"; shift ;;
    --bin-dir) BIN_DIR="${2:-}"; shift 2 ;;
    --bin-dir=*) BIN_DIR="${1#*=}"; shift ;;
    --no-bin) NO_BIN=true; shift ;;
    --force) FORCE=true; shift ;;
    --help|-h) usage; exit 0 ;;
    --version) echo "$PINNED_VERSION"; exit 0 ;;
    *) echo "install.sh: unknown option $1" >&2; usage >&2; exit 2 ;;
  esac
done

[[ -d "$TARGET" ]] || { echo "install.sh: target directory does not exist: $TARGET" >&2; exit 2; }
TARGET="$(cd "$TARGET" && pwd)"

installer_source="${BASH_SOURCE[0]}"
while [[ -h "$installer_source" ]]; do
  installer_dir="$(cd -P "$(dirname "$installer_source")" >/dev/null 2>&1 && pwd)"
  installer_source="$(readlink "$installer_source")"
  [[ "$installer_source" != /* ]] && installer_source="$installer_dir/$installer_source"
done
SCRIPT_DIR="$(cd -P "$(dirname "$installer_source")" 2>/dev/null && pwd || true)"
unset installer_source installer_dir
SOURCE_ROOT=""
DOWNLOAD_DIR=""
if [[ -n "$SCRIPT_DIR" && -f "$SCRIPT_DIR/VERSION" && -x "$SCRIPT_DIR/bin/taskspec" ]]; then
  SOURCE_ROOT="$SCRIPT_DIR"
else
  [[ "$MODE" != "symlink" ]] || { echo "install.sh: --symlink requires a local Task-Spec checkout" >&2; exit 2; }
  command -v curl >/dev/null 2>&1 || { echo "install.sh: curl is required for remote installation" >&2; exit 2; }
  command -v tar >/dev/null 2>&1 || { echo "install.sh: tar is required for remote installation" >&2; exit 2; }
  DOWNLOAD_DIR="$(mktemp -d -t taskspec-install-XXXXXX)"
  trap '[[ -n "$DOWNLOAD_DIR" ]] && rm -rf "$DOWNLOAD_DIR"' EXIT
  archive="$DOWNLOAD_DIR/task-spec.tar.gz"
  checksum="$DOWNLOAD_DIR/task-spec.tar.gz.sha256"
  release_base="${TASKSPEC_RELEASE_BASE_URL:-https://github.com/$REPOSITORY/releases/download/v$PINNED_VERSION}"
  asset_name="task-spec-$PINNED_VERSION.tar.gz"
  curl -fsSL "$release_base/$asset_name" -o "$archive"
  curl -fsSL "$release_base/$asset_name.sha256" -o "$checksum"
  expected_sha="$(awk 'NR == 1 {print $1}' "$checksum")"
  case "$expected_sha" in
    *[!0-9a-f]*|'') echo "install.sh: invalid release checksum manifest" >&2; exit 1 ;;
  esac
  if command -v shasum >/dev/null 2>&1; then
    actual_sha="$(shasum -a 256 "$archive" | awk '{print $1}')"
  elif command -v sha256sum >/dev/null 2>&1; then
    actual_sha="$(sha256sum "$archive" | awk '{print $1}')"
  elif command -v openssl >/dev/null 2>&1; then
    actual_sha="$(openssl dgst -sha256 "$archive" | awk '{print $NF}')"
  else
    echo "install.sh: SHA-256 provider required to verify the immutable release archive" >&2
    exit 2
  fi
  [[ "$actual_sha" == "$expected_sha" ]] || { echo "install.sh: release archive checksum mismatch" >&2; exit 1; }
  echo "verified: release archive sha256:$actual_sha"
  tar -xzf "$archive" -C "$DOWNLOAD_DIR"
  SOURCE_ROOT="$DOWNLOAD_DIR/task-spec-$PINNED_VERSION"
fi

SOURCE_VERSION="$(tr -d '[:space:]' < "$SOURCE_ROOT/VERSION")"
[[ "$SOURCE_VERSION" == "$PINNED_VERSION" ]] || { echo "install.sh: expected v$PINNED_VERSION, source is v$SOURCE_VERSION" >&2; exit 1; }

backup_existing() {
  local path="$1"
  if [[ -e "$path" || -L "$path" ]]; then
    if [[ "$FORCE" != true ]]; then
      echo "install.sh: refusing to clobber existing $path (use --force)" >&2
      return 1
    fi
    backup="${path}.backup.$(date -u +%Y%m%dT%H%M%SZ)"
    mv "$path" "$backup"
    echo "backup: $backup"
  fi
}

INSTALL_ROOT="${TASKSPEC_INSTALL_ROOT:-${HOME}/.local/share/task-spec}"
ENGINE_DEST="$INSTALL_ROOT/$PINNED_VERSION"
if [[ "$MODE" == "symlink" ]]; then
  if [[ -e "$ENGINE_DEST" || -L "$ENGINE_DEST" ]]; then
    if [[ -L "$ENGINE_DEST" && "$(readlink "$ENGINE_DEST")" == "$SOURCE_ROOT" ]]; then
      echo "kept: engine symlink $ENGINE_DEST"
    else
      backup_existing "$ENGINE_DEST"
      mkdir -p "$(dirname "$ENGINE_DEST")"
      ln -s "$SOURCE_ROOT" "$ENGINE_DEST"
    fi
  else
    mkdir -p "$(dirname "$ENGINE_DEST")"
    ln -s "$SOURCE_ROOT" "$ENGINE_DEST"
  fi
else
  if [[ -f "$ENGINE_DEST/VERSION" && "$(tr -d '[:space:]' < "$ENGINE_DEST/VERSION")" == "$PINNED_VERSION" && "$FORCE" != true ]]; then
    echo "kept: pinned engine $ENGINE_DEST"
  else
    [[ ! -e "$ENGINE_DEST" ]] || backup_existing "$ENGINE_DEST"
    mkdir -p "$ENGINE_DEST"
    for item in VERSION LICENSE README.md CHANGELOG.md SKILL.md agents assets bin configs src spec templates docs integrations .claude-plugin; do
      [[ -e "$SOURCE_ROOT/$item" ]] && cp -R "$SOURCE_ROOT/$item" "$ENGINE_DEST/$item"
    done
    echo "engine: $ENGINE_DEST"
  fi
fi

install_skill_copy() {
  local destination="$1"
  if [[ -e "$destination" || -L "$destination" ]]; then
    if [[ -f "$destination/.taskspec-version" && "$(cat "$destination/.taskspec-version")" == "$PINNED_VERSION" && "$FORCE" != true ]]; then
      if cmp -s "$SOURCE_ROOT/SKILL.md" "$destination/SKILL.md"; then
        echo "kept: $destination"
        return 0
      fi
    fi
    backup_existing "$destination" || return 1
  fi
  mkdir -p "$destination/references/schemas" "$destination/references/concepts"
  cp "$SOURCE_ROOT/SKILL.md" "$destination/SKILL.md"
  cp "$SOURCE_ROOT/docs/authoring-workflow.md" "$destination/references/authoring-workflow.md"
  cp "$SOURCE_ROOT/docs/quick-reference.md" "$destination/references/quick-reference.md"
  cp "$SOURCE_ROOT/docs/concepts/effort-gate.md" "$destination/references/concepts/effort-gate.md"
  cp "$SOURCE_ROOT/docs/concepts/signed-off.md" "$destination/references/concepts/signed-off.md"
  cp "$SOURCE_ROOT/spec/schemas/"*.json "$destination/references/schemas/"
  printf '%s\n' "$PINNED_VERSION" > "$destination/.taskspec-version"
  echo "skill:  $destination"
}

install_skill_link() {
  local destination="$1"
  if [[ -L "$destination" && "$(readlink "$destination")" == "$SOURCE_ROOT" ]]; then echo "kept: $destination"; return 0; fi
  [[ ! -e "$destination" && ! -L "$destination" ]] || backup_existing "$destination" || return 1
  mkdir -p "$(dirname "$destination")"
  ln -s "$SOURCE_ROOT" "$destination"
  echo "skill:  $destination -> $SOURCE_ROOT"
}

for destination in \
  "$TARGET/.agents/skills/task-spec" \
  "$TARGET/.claude/skills/task-spec" \
  "$TARGET/.grok/skills/task-spec"; do
  if [[ "$MODE" == "symlink" ]]; then install_skill_link "$destination"; else install_skill_copy "$destination"; fi
done

# Preserve the legacy Claude subagent entrypoint alongside the portable skill.
# The skill is the canonical authoring surface; this file is a compatibility
# door for existing checkouts and prompts that invoke `task-architect` directly.
architect_destination="$TARGET/.claude/agents/task-architect.md"
if [[ "$MODE" == "symlink" ]]; then
  if [[ -L "$architect_destination" && "$(readlink "$architect_destination")" == "$SOURCE_ROOT/agents/task-architect.md" ]]; then
    echo "kept: $architect_destination"
  else
    [[ ! -e "$architect_destination" && ! -L "$architect_destination" ]] || backup_existing "$architect_destination"
    mkdir -p "$(dirname "$architect_destination")"
    ln -s "$SOURCE_ROOT/agents/task-architect.md" "$architect_destination"
    echo "agent:  $architect_destination -> $SOURCE_ROOT/agents/task-architect.md"
  fi
else
  if [[ -f "$architect_destination" ]] && cmp -s "$SOURCE_ROOT/agents/task-architect.md" "$architect_destination" && [[ "$FORCE" != true ]]; then
    echo "kept: $architect_destination"
  else
    [[ ! -e "$architect_destination" && ! -L "$architect_destination" ]] || backup_existing "$architect_destination"
    mkdir -p "$(dirname "$architect_destination")"
    cp "$SOURCE_ROOT/agents/task-architect.md" "$architect_destination"
    echo "agent:  $architect_destination"
  fi
fi

if [[ "$NO_BIN" != true ]]; then
  mkdir -p "$BIN_DIR"
  launcher="$BIN_DIR/taskspec"
  if [[ -e "$launcher" || -L "$launcher" ]]; then
    if grep -q "task-spec launcher v$PINNED_VERSION" "$launcher" 2>/dev/null && [[ "$FORCE" != true ]]; then
      echo "kept: CLI launcher $launcher"
    elif grep -qE '^# task-spec launcher v[0-9]+\.[0-9]+\.[0-9]+$' "$launcher" 2>/dev/null && [[ "$FORCE" != true ]]; then
      # This is a launcher previously managed by Task-Spec, not an arbitrary
      # user executable. A version upgrade may safely repoint it to the new
      # side-by-side pinned engine without requiring destructive --force.
      printf '%s\n' '#!/usr/bin/env sh' "# task-spec launcher v$PINNED_VERSION" "exec \"$ENGINE_DEST/bin/taskspec\" \"\$@\"" > "$launcher"
      chmod +x "$launcher"
      echo "updated: CLI launcher $launcher"
    else
      backup_existing "$launcher"
    fi
  fi
  if [[ ! -e "$launcher" && ! -L "$launcher" ]]; then
    printf '%s\n' '#!/usr/bin/env sh' "# task-spec launcher v$PINNED_VERSION" "exec \"$ENGINE_DEST/bin/taskspec\" \"\$@\"" > "$launcher"
    chmod +x "$launcher"
    echo "cli:    $launcher"
  fi
  case ":$PATH:" in *":$BIN_DIR:"*) ;; *) echo "note: add $BIN_DIR to PATH" ;; esac
fi

for destination in "$TARGET/.agents/skills/task-spec" "$TARGET/.claude/skills/task-spec" "$TARGET/.grok/skills/task-spec"; do
  [[ -r "$destination/SKILL.md" ]] || { echo "install.sh: missing installed skill at $destination" >&2; exit 1; }
  grep -q '^name: task-spec$' "$destination/SKILL.md" || { echo "install.sh: invalid skill at $destination" >&2; exit 1; }
done
[[ -x "$ENGINE_DEST/bin/taskspec" ]] || { echo "install.sh: installed engine CLI is not executable" >&2; exit 1; }
[[ "$("$ENGINE_DEST/bin/taskspec" version)" == "$PINNED_VERSION" ]] || { echo "install.sh: installed engine failed its version check" >&2; exit 1; }
for destination in "$TARGET/.agents/skills/task-spec" "$TARGET/.claude/skills/task-spec" "$TARGET/.grok/skills/task-spec"; do
  cmp -s "$SOURCE_ROOT/SKILL.md" "$destination/SKILL.md" || { echo "install.sh: installed skill differs at $destination" >&2; exit 1; }
done
if [[ "$NO_BIN" != true ]]; then
  [[ "$("$launcher" version)" == "$PINNED_VERSION" ]] || { echo "install.sh: CLI launcher failed its version check" >&2; exit 1; }
fi

echo "Credentials: unchanged (Task-Spec never installs provider or model secrets)."
if [[ "$NO_BIN" != true ]]; then
  case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) echo "PATH: add $BIN_DIR, then enable completion with: taskspec completion bash|zsh|fish" ;;
  esac
fi
echo "Verify: taskspec doctor"
echo "Prove:  taskspec demo"
echo "INSTALL=OK"
