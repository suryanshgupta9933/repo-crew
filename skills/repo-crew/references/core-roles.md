# Cross-cutting roles

Domain agents own slices of the repo. Cross-cutting roles own a *concern* that spans slices. Include each only when the repo gives a reason. Names below are defaults; use the repo's vocabulary when natural.

Each role has a fixed agent slug, so two crews of the same shape name the same agent the same way:

| Role | Slug |
|---|---|
| docs-and-decisions keeper | `crew-keeper` |
| shipper | `shipper` |
| reviewer | `reviewer` |
| architect / planner | `architect` |
| security & privacy | `security-review` |
| QA / test | `qa` |
| release / infra | `release` |

Slugs are the domain's own words, never prefixed with the project name.

## Contents
- docs-and-decisions keeper
- shipper
- reviewer
- architect / planner
- security & privacy
- QA / test
- release / infra
- Tool profiles

## docs-and-decisions keeper

**Include:** almost always. It is what keeps the other agents coherent over time.

**Owns:** `docs/crew/**` — `DECISIONS.md`, `ROSTER.md`, shared knowledge files — plus applying knowledge-file updates proposed by other agents and running the drift check. It edits the repo's own README or docs only when the user asks for it.

**Rules:**
- Records a decision only when the user states or confirms it; otherwise logs it as `proposed` (see `decisions.md`).
- On every handoff received, decides which docs/knowledge/ledger entries change and edits them, bumping `verified_at` via `check_drift.py --stamp`.
- Flags contradictions between a requested change and a `locked` decision back to the orchestrator instead of resolving them.

## shipper

**Include:** if the repo has CI, tests, a lint/typecheck step, or the user wants a PR workflow.

**Discover the gate, never invent it.** Derive required checks from CI workflow files, Makefile/justfile/package scripts, pre-commit config. Write the resolved commands into its knowledge file with the source of each. If a command cannot be found or run, record that explicitly.

**Protocol:**
1. Confirm the work is on a feature branch; never push directly to the default branch.
2. Run the full local gate that mirrors CI (lint, types, tests, build). Fix failures it caused, or report them with the failing command and output; never skip, weaken or disable a check to get green. It does not fix product source outside its own domain.
3. Check the diff against `DECISIONS.md` for locked-decision violations; stop and report if any.
4. Open a PR (e.g. via `gh`) with a body listing: what changed and why, which domains were touched, gate results, decisions referenced, follow-ups.
5. Return a `HANDOFF` block asking the orchestrator to dispatch the docs-and-decisions keeper (always) plus any owner whose knowledge file `covers` changed paths.
6. Merge only if the user explicitly asks; otherwise leave the PR open.

**Tools:** Bash, Read, Edit (for fixing lint-level issues), Grep, Glob.

## reviewer

**Include:** once the repo has several invariants or locked decisions worth enforcing. A generic reviewer exists already; this one's value is the *project-specific* checklist.

**Spec:** read-only. Builds its checklist from `docs/crew/*.md` invariants and `DECISIONS.md`. Reports findings by severity with file:line, distinguishes "violates a locked decision" (blocking) from "style/preference" (non-blocking). If a code-quality or reuse skill was named by the user, apply it here.

**Tools:** Read, Grep, Glob, Bash (read-only commands such as git diff/log).

## architect / planner

**Include:** when cross-domain changes are common, when several domains share contracts, or when the user plans large features. Skip for repos where changes stay inside one domain.

**Spec:** read-only on code; holds the whole map via `docs/crew/shared/` architecture and data-flow notes. Produces a plan that names which agents do which steps and in what order, plus contracts that must not break. Writes plans to a doc only when asked.

**Tools:** Read, Grep, Glob (Write only for plan docs if the user wants them persisted).

## security & privacy

**Include:** when the product handles credentials, PII, regulated data, untrusted input, sandboxed execution, network egress, or has compliance requirements.

**Spec:** read-mostly; owns the data-handling rules (what may be logged, stored, transmitted, retained; where secrets live). Has *review authority*: other agents' handoffs touching its `covers` paths include a request for its review. Findings that violate a stated rule are blocking. Rules come from the user (interview step 3) and are tagged `[user]`, never inferred.

**Tools:** Read, Grep, Glob, Bash (read-only).

## QA / test

**Include:** non-trivial test infra (e2e, browser tests, fixtures, flaky suites) or recurring regressions.

**Spec:** owns test strategy, fixtures, flake triage. Writes and edits tests; avoids editing product code except for testability seams, and says so in the handoff.

## release / infra

**Include:** separate deploy pipeline, packaging, versioning, store submissions, infra-as-code.

**Spec:** owns release checklist, versioning rules, changelog, deploy config. Consumes the shipper's PR output; keeps release steps in its knowledge file with the source of each command.

## Tool profiles (defaults)

| Profile | Tools | For |
|---|---|---|
| read-only | Read, Grep, Glob (+ read-only Bash) | reviewer, architect, security |
| owner | Read, Grep, Glob, Edit, Write, Bash | domain owners, QA, docs keeper |
| shipper | Read, Grep, Glob, Edit, Bash | shipper, release |

Omit the `tools` field only if the agent genuinely needs everything, including MCP tools. Otherwise an allowlist is safer and clearer.
