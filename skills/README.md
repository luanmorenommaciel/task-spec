# Task-Spec skills pack

One product skill: [`task-spec`](task-spec/SKILL.md).

Root [`SKILL.md`](../SKILL.md) is the authoring source. The pack file is a
byte-for-byte copy. Do not add hop skills or Converge passes.

## Install dests

`install.sh` copies that skill to four dests:

- `.agents/skills/task-spec`
- `.claude/skills/task-spec`
- `.grok/skills/task-spec`
- `.cursor/skills/task-spec`

`--global` uses `$HOME` as the target.
