# Installation by harness

The canonical installer writes equivalent skill content to all supported local
harness destinations. It never stores model/provider credentials.

```bash
curl -fsSL https://raw.githubusercontent.com/luanmorenommaciel/task-spec/main/install.sh | bash
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
checkout. `--force` backs up a managed destination before replacement.

For npm/GitHub:

```bash
npm install -g github:luanmorenommaciel/task-spec#v3.6.0
taskspec-install
```

For Claude marketplace:

```text
/plugin marketplace add luanmorenommaciel/task-spec
/plugin install task-spec@taskspec
```
