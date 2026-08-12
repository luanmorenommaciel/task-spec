# Installation by harness

The canonical installer writes equivalent skill content to all supported local
harness destinations. It never stores model/provider credentials.

Until the `v3.7.0` release tag is published, install from a checkout:

```bash
git clone --depth 1 https://github.com/luanmorenomaciel/task-spec.git \
  "$HOME/.local/share/task-spec-src"
bash "$HOME/.local/share/task-spec-src/install.sh" --target /path/to/repo --copy
export PATH="$HOME/.local/bin:$PATH"
taskspec doctor
taskspec demo
```

After the tag exists and its remote-install smoke workflow passes, the pinned
curl door is:

```bash
curl -fsSL \
  https://raw.githubusercontent.com/luanmorenomaciel/task-spec/v3.7.0/install.sh \
  | bash -s -- --target /path/to/repo
```

| Harness | Installed skill |
|---|---|
| Codex and Kimi | `.agents/skills/task-spec/SKILL.md` |
| Claude Code | `.claude/skills/task-spec/SKILL.md` |
| Grok Build | `.grok/skills/task-spec/SKILL.md` |

Useful installer controls:

```bash
bash install.sh --target /path/to/repo --copy
bash install.sh --target /path/to/repo --symlink
bash install.sh --bin-dir "$HOME/bin"
bash install.sh --no-bin
bash install.sh --force
```

Copy mode is pinned and non-clobbering. Symlink mode is only for a local
checkout. `--force` backs up a managed destination before replacement. The
installer prints `INSTALL=OK` only after engine, skill parity, and launcher
version checks pass.

For npm/GitHub:

```bash
npm install -g github:luanmorenommaciel/task-spec#v3.7.0
taskspec-install
```

This GitHub tag door is also pending until the release tag and remote smoke
workflow exist. Local package construction and installation are covered by
`make check`.

For Claude marketplace:

```text
/plugin marketplace add luanmorenommaciel/task-spec
/plugin install task-spec@taskspec
```
