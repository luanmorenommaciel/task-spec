# adapters/trackers — backlog tracker integrations

A *tracker* is where the backlog of task-specs lives and how status moves
through it.

## Local tracker (works today)

The local tracker is simply a `tasks/` directory in your repo:
`tasks/T-*.md` files (the specs) + `_state.yaml` (derived index) +
`_metrics.jsonl` (append-only ledger) + `done/` / `parked/` / `queue/`
subdirs. The engine's backlog scripts (`taskspec ready`, `transition`,
`rebuild-state`, `archive`, `backup`, `lint`, `metrics`) operate on it
directly. `_state.yaml` is always rebuildable from frontmatter —
`taskspec rebuild-state` — so the markdown files stay the source of truth.

## External trackers (roadmap)

GitHub Issues, Linear, and Jira adapters are **to be rebuilt on MCP** — one
thin MCP client (create / transition / link) instead of bespoke per-tracker
code. See **P2-3** in [`../../TODO.md`](../../TODO.md). Until then, mirror
ids by hand: the `linear_ref:` frontmatter field is the designated off-repo
Intent crossing for an external ticket id/URL.
