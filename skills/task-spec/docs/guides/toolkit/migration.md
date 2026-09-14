# Seamwise cutover and rollback

Native authoring uses TaskSpec-owned decomposition code and never shells out to
Seamwise. There is no compatibility command facade. Keep the original workspace
and use an explicit destination initiative:

```bash
taskspec --dry-run decompose import <id> --source /path/to/legacy-workspace
taskspec decompose import <id> --source /path/to/legacy-workspace
```

The importer requires the original authored recipe, preserves original IDs and
artifacts under `migration/original`, and records source file digests. It rejects
unsafe paths and symlinks. Already sealed or accepted TaskSpecs remain untouched.
New native materialization requires fresh native review and HMAC authorization.
Review import diagnostics before continuing; a Boolean legacy approval is insufficient.

Rollback before materialization means retaining the original workspace and removing
only the newly imported initiative after checking its migration receipt. After
materialization, retain accepted records and sealed tasks; stop new native dispatch
and review successor work as needed. Do not rewrite historical receipts or silently
convert workspaces back. Interrupted plan replacement retains `.<initiative>.previous` beside the initiative; inspect both trees before recovery.
