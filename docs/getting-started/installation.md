# Installation by harness

The canonical installer writes equivalent skill content to all supported local
harness destinations. It never stores model/provider credentials.

Until the `v3.8.0` release tag is published, install from a checkout:

```bash
git clone --depth 1 https://github.com/luanmorenomaciel/task-spec.git \
  "$HOME/.local/share/task-spec-src"

# User-level skills for Codex/Kimi, Claude Code, and Grok Build
bash "$HOME/.local/share/task-spec-src/install.sh" --global --copy
export PATH="$HOME/.local/bin:$PATH"
taskspec doctor
taskspec demo
```

For repository-local skill copies instead:

```bash
bash "$HOME/.local/share/task-spec-src/install.sh" \
  --target /path/to/repository --copy
```

After the tag exists and its remote-install smoke workflow passes, the pinned
curl door is:

```bash
curl -fsSL \
  https://raw.githubusercontent.com/luanmorenomaciel/task-spec/v3.8.0/install.sh \
  | bash -s -- --global
```

| Harness | User-level skill | Repository-local skill |
|---|---|---|
| Codex and Kimi | `~/.agents/skills/task-spec/SKILL.md` | `.agents/skills/task-spec/SKILL.md` |
| Claude Code | `~/.claude/skills/task-spec/SKILL.md` | `.claude/skills/task-spec/SKILL.md` |
| Grok Build | `~/.grok/skills/task-spec/SKILL.md` | `.grok/skills/task-spec/SKILL.md` |

Useful installer controls:

```bash
bash install.sh --global --copy
bash install.sh --target /path/to/repo --copy
bash install.sh --target /path/to/repo --symlink
bash install.sh --bin-dir "$HOME/bin"
bash install.sh --no-bin
bash install.sh --force
```

Copy mode is pinned and non-clobbering. Symlink mode is only for a local
checkout. `--force` backs up a managed destination before replacement. The
installer prints `INSTALL=OK` only after engine, skill parity, and launcher
version checks pass. The remote door downloads the release asset and published
SHA-256, verifies the archive before extraction, reports PATH when needed, and
points to shell completion.

`--global` is an explicit user-level alias: it targets the current user's home
directory, writes the three supported harness skill locations plus Claude's
compatibility agent, and uses `~/.local/bin` for the launcher. It does not write
credentials or modify shell startup files.

For npm/GitHub:

```bash
npm install -g github:luanmorenommaciel/task-spec#v3.8.0
taskspec-install --global
```

This GitHub tag door is also pending until the release tag and remote smoke
workflow exist. Local package construction and installation are covered by
`make check`.

For Claude marketplace:

```text
/plugin marketplace add luanmorenommaciel/task-spec
/plugin install task-spec@taskspec
```
