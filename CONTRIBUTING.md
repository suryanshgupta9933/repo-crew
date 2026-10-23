# Contributing

Thanks for improving `repo-crew`. Issues and PRs are both welcome.

## Reporting a problem

The most useful issue reports include:

- the shape of the repo you tried it on (monorepo, polyglot, single package, existing agents/ADRs),
- what the crew plan proposed and which parts were wrong,
- the repo-crew version (`claude plugin list`).

If a script misbehaves, include the output of:

```bash
python skills/repo-crew/scripts/survey_repo.py . --json
```

## Development

```bash
git clone https://github.com/suryanshgupta9933/repo-crew.git
cd repo-crew
```

Try your change against a scratch repo before opening a PR:

```bash
claude --plugin-dir .
```

Then run the checks:

```bash
python -m py_compile skills/repo-crew/scripts/*.py
python skills/repo-crew/scripts/survey_repo.py . > /dev/null
python skills/repo-crew/scripts/check_drift.py . > /dev/null
claude plugin validate --strict .
```

CI runs these plus a version/CHANGELOG consistency check.

## Releasing

`plugin.json` sets a `version`, and a marketplace install stays pinned to that string until it changes. So a release is: bump the version, add the changelog entry, tag. If you skip the bump, nobody receives the update.

1. Bump `version` in `.claude-plugin/plugin.json`. It must match the top entry in `CHANGELOG.md` — CI fails otherwise.
2. Add a `CHANGELOG.md` section for the new version.
3. Commit, tag (`v0.1.0`), and push the tag.

Do not set `version` in the marketplace entry. The plugin manifest takes precedence, and having both is a source of confusion.

If you would rather have users track commits instead of versions, delete the `version` field from `plugin.json` entirely — Claude Code then resolves updates from the commit SHA. You cannot do both.

## Changing the skill

- The `SKILL.md` frontmatter is limited to the six Agent Skills standard fields: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Any other key is a hard packaging error on claude.ai and the Skills API.
- Keep `SKILL.md` under 500 lines and push detail into `references/`.
- Keep `skills/repo-crew/` self-contained — no references to paths outside the skill directory.
- Update `skills/repo-crew/evals/evals.json` when you change behaviour.
- If you change the output shape, update `examples/sample-output/`.
- The scripts are standard-library only and must keep working on Python 3.9+.

## Commit messages

Write plain, descriptive commit messages explaining what changed and why. No generated attribution lines.
