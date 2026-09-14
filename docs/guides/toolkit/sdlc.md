# Release and maintenance evidence

The planning, design, build, test, deployment, and maintenance stages use the same
atomic lifecycle. Release and monitoring remain in existing external systems.
A release-readiness task should bind exact source revision and artifact digest,
target environment, CI/CD run, required checks, rollback evidence, and the human
release decision. Its evals verify those claims at the appropriate target.

```bash
taskspec example release-evidence --out release-input.json
taskspec receipt operational validate release-input.json
taskspec receipt operational import release-input.json --out .taskspec/operations/release.json
```

Operational imports retain source digests and reported provenance. `--verify-local`
checks attachment bytes against declared digests; it does not authenticate the
external reporter or verify target health. Import never grants acceptance.
Use a separate authorized task to independently verify the target when required.

For incidents, use `taskspec example incident --out incident.json`, record the
actual observation, affected revision, environment, impact, and source, then import
it with the same receipt command. `decompose init <id> --intent-file incident.json`
creates candidate intent. Diagnose with a bounded diagnose-repair-verify recipe.
Regression additions, policies, skills, and project knowledge changes require
reviewed scoped tasks; observation alone never authorizes them.

The lifecycle mapping is informed by [Anthropic's AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook).
TaskSpec's contracts and acceptance boundaries are implementation choices.
