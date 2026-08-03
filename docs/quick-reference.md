# Task-Spec Quick Reference

> One-page cheatsheet for daily Task-Spec operations.
> See [index.md](index.md) for full KB navigation.

---

## Generate a new Task-Spec

```bash
# Required: slug, effort (S or M)
# Optional: agent (default: any), source_note
taskspec new \
    verify-langfuse-otel S any notes/2026-05-04.md
```

## Validate before commit

```bash
taskspec validate tasks/T-*.md
```

## Status transitions (atomic)

```bash
taskspec transition T-XXX in-progress
taskspec transition T-XXX done
taskspec transition T-XXX parked "budget exhausted"
```

## List ready tasks

```bash
taskspec ready
taskspec ready --effort=S
taskspec ready --agent=any
```

## Recovery

```bash
# Rebuild _state.yaml from frontmatter (truth)
taskspec rebuild-state

# Move done/parked to subdirs
taskspec archive

# Snapshot the backlog
taskspec backup
```

---

## YAML frontmatter — required fields

```yaml
---
id: T-YYYYMMDD-kebab-slug
title: One-line imperative
status: ready                  # ready | in-progress | blocked | done | parked
format_version: 3
profile: standard              # lite | standard | full (absent → standard)
effort: S                      # S | M (L/XL refused; route to AgentSpec)
budget_iterations: 15
agent: any                     # any | python-developer | ...
parent: (none)                 # FEATURE-altitude PRD/SDD this task distills from
depends_on: []
touches_paths:
  - path/to/file
source_note: notes/...md
created: 2026-05-19T00:00:00Z
tags: [...]
signed_off: false              # flipped true ONLY by safe-to-delegate.sh --stamp
signed_off_by: (none)
signed_off_at: (none)
accepted: false                # flipped true by accept-task.sh AFTER execution
---
```

---

## The v3 zones

```text
Intent:        ## Goal + ## Context          (lean, ≤100 lines)
Behavior:      ## Behavior                   (B-1, B-2 … Given/When/Then; standard/full)
Contract:      ## Success Criteria           (≥3 runnable bash evals; each verifies: [B-N])
               ## Validation Card            (YAML mirror; success_criteria + retry + agent_contract)
               ## Exit Check                 (combined bash one-liner)
Rollback:      ## Rollback Plan              (reversal steps; required at full)
Observability: ## Observability Hooks        (duration/metric/alert; required at full)
Guardrails:    ## Anti-Patterns              (specific don'ts)
               ## Do-Not-Touch               (exact paths)
Operations:    ## Open Questions             (admit unknowns)
```

Profiles scale which zones are required (`lite` < `standard` < `full`); the
irreducible core at every profile is **Goal + Success Criteria + Exit Check**.
For `standard`/`full`, the **behavior ↔ eval** chain is enforced both ways (no
orphan B-N, no orphan eval). See [concepts/profiles.md](concepts/profiles.md)
and [concepts/six-zones.md](concepts/six-zones.md).

---

## Eval pattern reminders

```bash
# Cheapest first; fail fast
eval_1() { test -f path/to/file; }           # presence  (1ms)
eval_2() { grep -q "thing" path/to/file; }   # content   (10ms)
eval_3() { curl -fs http://x | jq -e '.ok'; }# behavior  (500ms)
eval_4() { pytest -q tests/path; }           # tests     (30s)
```

---

## Routing rules

| Task is... | Use |
|------------|-----|
| S or M effort, bash-checkable success | **Task-Spec (EDD)** |
| L or XL effort | AgentSpec (SDD) |
| Subjective output (UI feel, copy) | AgentSpec (SDD) |
| One-off exploration ("what would X look like?") | Just prompt; no spec needed |

---

## Version history

The format ships at v3 today (HMAC sign-off envelope, effort-scaled profiles, the
Behavior zone + traceability, conformance levels, `accept-task.sh`, `requires:`
acceptance gate, `backend_metadata`). For what shipped in each release, see
[CHANGELOG.md](../CHANGELOG.md).

---

## Anti-patterns (don't)

- ❌ Edit frontmatter directly — use `taskspec transition`
- ❌ Author L/XL as Task-Spec — refused; use AgentSpec
- ❌ Skip evals for "simple" tasks — every spec needs ≥3
- ❌ Verbose Zone 1 (>100 lines Context) — you wrote a PRD
- ❌ Vague Zone 3 ("be careful") — be specific
- ❌ Print secrets in evals or do-not-touch — redact always
