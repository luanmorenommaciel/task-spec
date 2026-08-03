# AGENTS.md — using the taskspec CLI from a Codex host

task-spec is an engine, not a prompt pack. Drive it through the `taskspec` CLI
(on PATH, or invoke `bin/taskspec` from a checkout of this repo).

## The 5 core commands

```bash
taskspec new <slug> <effort> [agent] [source]   # scaffold tasks/T-*.md from the template
taskspec validate <spec>                        # structural lint (no stamping)
taskspec gate --stamp <spec>                    # PRE-gate: seal evals (HMAC) + signed_off:true
taskspec run --ci <spec>                        # execute evals; one JSON object per eval
taskspec accept --stamp <spec>                  # POST-gate: re-run evals + blast radius → accepted:true
```

Supporting: `taskspec ready` (claimable tasks), `taskspec transition <id>
<status>`, `taskspec doctor` (toolchain check), `taskspec version`.

## Exit codes (the contract to branch on)

- `0` — pass / DELEGATE / ACCEPT
- `1` — a check failed (structural error, eval RED, blast-radius breach, HMAC mismatch)
- `2` — usage error (bad command or missing file)

Machine-readable lines: `gate` prints `TIER=1|2` for a signed spec,
`accept` prints `ACCEPTED=1|0`, `run --ci` prints `{"eval","status",...}` per eval.

## Rules for a Codex executor

- Never hand-edit `signed_off*` or `accepted*` frontmatter — the envelope check
  rejects hand-stamping; only `gate --stamp` / `accept --stamp` write them.
- Honor `touches_paths` / `## Do-Not-Touch`: the POST-gate diffs the change set
  and rejects out-of-scope edits.
- On `budget_iterations` exhausted: set `status: parked` with a
  `blocked_reason` — do not loop forever.
