# Changelog

All notable changes to this project are documented here.

The version here must match `version` in `.claude-plugin/plugin.json`. Marketplace installs stay pinned
to that string until it changes, so a release without a bump reaches nobody.

## 0.1.0

Initial release.

- `repo-crew` skill with four modes: init, audit, refresh, add.
- `scripts/survey_repo.py` — deterministic repo survey (units, churn, co-change, CI and test signals).
- `scripts/check_drift.py` — stale-knowledge and uncovered-path detector, with `--stamp` to record verification.
- `references/` — crew-sizing tests, cross-cutting roles, agent and knowledge templates, orchestrator block, decision ledger, maintenance.
- `evals/evals.json` — example prompts with expected behaviour.
- Single-plugin marketplace (`repo-crew-marketplace`) sourcing the plugin from the repo root.
- CI: manifest parsing, script compile, frontmatter portability rules, version/CHANGELOG sync, `claude plugin validate --strict`.
