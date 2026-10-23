# Maintaining the crew

A crew that is not maintained turns into confident misinformation. This file covers drift checks, audits, changing the roster, and routing tests.

## Contents
- Drift check (refresh mode)
- Audit mode
- Add, split, merge, retire
- Routing evals
- When to run what

## Drift check (refresh mode)

```bash
python scripts/check_drift.py <repo>              # report
python scripts/check_drift.py <repo> --json
python scripts/check_drift.py <repo> --stamp docs/crew/<slug>.md   # set verified_at to HEAD
```

The report lists, per knowledge file: commits and files changed under its `covers` globs since `verified_at`, and files in the repo that no knowledge file covers (ranked by directory).

Procedure for each stale file:
1. Read the commits that touched its paths (`git log --stat <verified_at>..HEAD -- <globs>`).
2. Re-read the affected code. Update invariants, map, commands and gotchas that changed; delete facts that are no longer true.
3. Re-tag facts honestly (`[code]` only if you re-verified).
4. Run `--stamp` only after the content is actually reconciled; stamping without reading defeats the check.

For uncovered paths: decide whether they belong to an existing agent (extend `covers`), form a new domain (see add), or are intentionally uncovered (generated, vendored; note it in ROSTER.md).

## Audit mode

Run when the repo changed shape: new runtime, big refactor, several new top-level directories, agents frequently misrouted, or every few months.

1. Re-run the survey and the drift check.
2. Re-apply the three crew tests (`survey.md`) to every agent and to uncovered high-churn units. Note any that no longer pass.
3. Check every `locked` decision against the code.
4. Propose changes as a short plan: agents to add, split, merge, retire; knowledge files to refresh; decisions to confirm. Get the user's agreement before editing.
5. Apply, update ROSTER.md and the CLAUDE.md block, re-run routing evals, stamp refreshed files.

## Add, split, merge, retire

- **Add:** run the tests, create agent file + knowledge file, extend ROSTER and the CLAUDE.md table, add routing evals for it, and adjust neighbors' "Not for" lines so they point to it.
- **Split:** move the relevant facts into the new knowledge file, narrow the old `covers`, update both descriptions' "Not for", re-run evals for both.
- **Merge:** combine knowledge files (dedupe, keep `[user]` facts), union `covers`, delete the redundant agent file, redirect references in other agents' "Not for" lines.
- **Retire:** delete the agent and knowledge file only after confirming with the user; record why in ROSTER's "Considered and merged" so a future audit does not recreate it.

## Routing evals

`docs/crew/routing-evals.md` format:

```markdown
| # | Request | Expected agent | Expected handoffs |
|---|---|---|---|
| 1 | "Make the panel show tool errors inline" | side-panel-ui | docs-keeper |
| 7 | "Add a new tool and surface it in the panel" | agent-harness | side-panel-ui, docs-keeper |
```

Generate:
- 3 realistic requests per agent, phrased like a user would, using the repo's vocabulary but not copying the description's wording.
- 3-5 cross-domain requests with a primary agent and expected handoffs.
- 2 requests that conflict with a locked decision, expecting a stop and a `needs-decision` handoff.
- 1-2 "ship it" requests, expecting the shipper path.

Test procedure: for each request, decide which agent the dispatch rules and descriptions would select, and why. Where it differs from expected, fix the **description or routing table**, not the test. Re-run the failing rows. If subagents are available, also dispatch each agent with a read-only domain question and check that it reads its knowledge file and that its answer is consistent with it.

Tests that always pass and tests that always fail are both uninformative; rewrite them to probe the boundary between two neighbors.

## When to run what

| Trigger | Action |
|---|---|
| After merging a notable PR | shipper hands off to docs keeper; refresh affected file |
| Weekly or before a release | drift check |
| New top-level directory or runtime | add or audit |
| Wrong agent chosen twice | fix description; re-run evals |
| User reverses a decision | docs keeper supersedes entry (with user's explicit say-so) |
