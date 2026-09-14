# Native Claude skill loading correction

The restricted qualification profile did not advertise the copied project skill.
Most initial observations read the skill file manually; the denied-work Claude
journey skipped it entirely. Those results cannot establish native skill discovery.
The eight guarded observations remain under `chat-guarded/`, with seven bounded
behavioral passes and one skill-activation failure. The failed original atomic
journey remains under `chat-corrected/` and is not replaced by these runs.

Explicit native plugin discovery then identified a product defect: both plugin
manifests pointed `skills` at `./SKILL.md`, but the native loader requires a
containing directory. The corrected entry is `.`. The pinned Claude 2.1.270
probe advertised `task-spec:task-spec`, invoked the native Skill tool, and found
its guides relative to the plugin root. See `native-plugin-probe/` for the
original load error, corrected manifest, and actual invocation trace.

Installation now checks plugin versions and valid contained skill directories,
and includes `.claude-plugin/` in its resource-integrity inventory. The installed
regression rejects file entries, stale versions, and manifest drift. A fresh
237-resource toolkit installation passed and its native plugin entry loaded
without errors. These are loading and packaging checks, not complete behavioral
qualification; the remaining fresh chat cases still require actual review.

The qualification profile loads the installed package through `--plugin-dir`
while preserving restricted mode, existing permissions, and the deny-and-stop
guard. No globally installed plugin or user setting is changed by this selection.

Primary references: [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference)
and [hook reference](https://code.claude.com/docs/en/hooks).
