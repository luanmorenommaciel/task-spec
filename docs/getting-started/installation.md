# Installation by harness

The canonical installer writes equivalent skill content to all supported local
harness destinations. It never stores model/provider credentials.

The repository is private. Authenticate GitHub before cloning; until `v3.8.1`
clears its evidence gate and the final tag is published, install from a
checkout:

```bash
git clone --depth 1 https://github.com/luanmorenommaciel/task-spec.git \
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

For a checksum-backed installation of the published `v3.8.0` release:

```bash
gh auth status
release_dir="$(mktemp -d)"
gh release download v3.8.0 \
  --repo luanmorenommaciel/task-spec \
  --pattern 'task-spec-3.8.0.tar.gz*' \
  --dir "$release_dir"
(cd "$release_dir" && shasum -a 256 -c task-spec-3.8.0.tar.gz.sha256)
tar -xzf "$release_dir/task-spec-3.8.0.tar.gz" -C "$release_dir"
bash "$release_dir/task-spec-3.8.0/install.sh" --global --copy
```

Anonymous raw-file and release-asset URLs do not work while the repository is
private. The release workflow authenticates the Contents and release APIs,
then exercises the tagged installer against the published checksum assets.
Each private release also carries an Ed25519-signed DSSE/in-toto provenance
statement. Its public verification key is retained at
`release/trust/release-provenance.ed25519.pub.pem`; the private key exists only
in the trusted GitHub Actions secret store.

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
gh auth setup-git
npm install -g git+https://github.com/luanmorenommaciel/task-spec.git#v3.8.0
taskspec-install --global
```

The authenticated GitHub tag door and local package construction are covered by
the hosted release smoke and `make check`, respectively.

For Claude marketplace:

```text
/plugin marketplace add luanmorenommaciel/task-spec
/plugin install task-spec@taskspec
```
