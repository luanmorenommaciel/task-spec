# TaskRevision/v1

`TaskRevision/v1` is the stable identity of one authorized Task-Spec revision:

```text
sha256("TaskRevision/v1\n" + task_id + "\n" + body_digest + "\n" + authority_manifest_digest)
```

The authority manifest is canonical JSON of the complete frontmatter excluding
only these mutable operational fields:

- lifecycle and planning: `status`, `blocked_reason`, `owner`, `priority`,
  `due_date`, `tags`;
- external projections: `tracker_ref`, deprecated `linear_ref`, `projection`;
- authorization storage: `signed_off`, `signed_off_by`, `signed_off_at`,
  `signed_off_sig`;
- acceptance bookkeeping: `accepted`, `accepted_by`, `accepted_at`,
  `accepted_tier`, `accepted_attempt_id`, `accepted_authorization_ref`,
  `acceptance_record_digest`.

Everything else is sealed, including unknown future fields. Mappings are
key-sorted; list order is retained; scalars are normalized to canonical UTF-8
JSON. Duplicate keys, aliases, unsupported tags, and ambiguous YAML fail.

```bash
python3 src/security/task_revision.py tasks/T-…-leaf.md
python3 src/security/task_revision.py tasks/T-…-leaf.md \
  --field task_revision_digest
```

The normative structure is
[`task-revision.schema.json`](../../spec/schemas/task-revision.schema.json).
