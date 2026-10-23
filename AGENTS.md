# AGENTS.md

Instructions for coding agents working on this repository.

## What this repo is

`repo-crew` is a Claude Code plugin containing one skill, `repo-crew`. The skill audits a target repository and generates a crew of specialist subagents plus committed per-domain knowledge files, a decision ledger and a shipping gate.

## Where things are

| Path | Purpose |
|---|---|
| `.claude-plugin/plugin.json` | Plugin manifest. `version` here pins what users get. |
| `.claude-plugin/marketplace.json` | Marketplace manifest. The single entry sources the plugin from `"./"` (the repo root). |
| `skills/repo-crew/SKILL.md` | The skill. Frontmatter is restricted to the six Agent Skills standard fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`) because claude.ai and the Skills API hard-error on anything else. |
| `skills/repo-crew/references/` | Progressive-disclosure detail files. One topic per file, loaded on demand. |
| `skills/repo-crew/scripts/` | `survey_repo.py` and `check_drift.py`. Standard library only, no dependencies. |
| `skills/repo-crew/evals/evals.json` | Example prompts with expected behaviour. |
| `examples/sample-output/` | Illustrative output for a made-up project. Never edit to match real output. |

## Rules

- **Do not add runtime dependencies.** The scripts must stay stdlib-only so they run anywhere Python 3.9+ exists.
- **Do not add a `CLAUDE.md` at the repo root.** `claude plugin validate` warns about one, and it is not loaded as plugin context anyway.
- **Keep `skills/repo-crew/` self-contained.** Nothing in the skill may reference a path outside its own directory, so `cp -r skills/repo-crew ~/.claude/skills/` keeps working.
- **Bump the version on every release.** See [CONTRIBUTING.md](CONTRIBUTING.md). Users on a marketplace install stay pinned to the version string in `plugin.json`.
- **Keep the `description` under 1024 characters** and `compatibility` under 500. Both are hard limits.

## Before you open a PR

```bash
python -m py_compile skills/repo-crew/scripts/*.py
python skills/repo-crew/scripts/survey_repo.py . > /dev/null
claude plugin validate --strict .
```

CI runs the first three plus a check that the version in `plugin.json` matches the top entry in `CHANGELOG.md`.
