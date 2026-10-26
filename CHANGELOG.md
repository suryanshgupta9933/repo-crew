# Changelog

All notable changes to this project are documented here.

The version here must match `version` in `.claude-plugin/plugin.json`. Marketplace installs stay pinned
to that string until it changes, so a release without a bump reaches nobody.

## 0.1.1

- Drift checker no longer skips all of `docs/` — only the crew's own `docs/crew/`. A repo's own `docs/` is now eligible for an agent to own, and shows up in the uncovered report when nobody does.
- Fixed agent naming: agents are named `<domain-slug>` with no project-name prefix, and the cross-cutting roles have fixed slugs (`crew-keeper`, `shipper`, `reviewer`, `architect`, `security-review`, `qa`, `release`), so two crews of the same shape name the same agent the same way.
- README documents what a run costs: roughly ten minutes and a few dollars of model spend on a ~230-file repository for a full init, with audit and refresh far cheaper.

## 0.1.0

Initial release.

- `repo-crew` skill with four modes: init, audit, refresh, add.
- `scripts/survey_repo.py` — deterministic repo survey (units, churn, co-change, CI and test signals).
- `scripts/check_drift.py` — stale-knowledge and uncovered-path detector, with `--stamp` to record verification.
- `references/` — crew-sizing tests, cross-cutting roles, agent and knowledge templates, orchestrator block, decision ledger, maintenance.
- `evals/evals.json` — example prompts with expected behaviour.
- Single-plugin marketplace (`repo-crew-marketplace`) sourcing the plugin from the repo root.
- CI: manifest parsing, script compile, frontmatter portability rules, version/CHANGELOG sync, `claude plugin validate --strict`.
