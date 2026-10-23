# Surveying a repo and deciding the crew

## Contents
1. Running and reading the survey
2. What to read beyond the script
3. Finding domain boundaries
4. Deciding the crew (the three tests)
5. Sizing: typical outcomes, not limits
6. Split and merge triggers

## 1. Running and reading the survey

```bash
python scripts/survey_repo.py <repo> [--days 180] [--json]
```

It reports: languages and LOC, manifests, CI/ship signals, existing agent config, "units" (top-level or container-aware directories) with file counts, LOC and recent commit counts, co-change pairs, entry-point-like files, and largest files. Treat it as a map, not a verdict:

- **Units with high LOC and high churn** are the likeliest agent domains.
- **Co-change pairs** (units that change in the same commits) show hidden coupling. Strongly coupled units usually belong to one agent, or need a shared knowledge file describing the contract between them.
- **Low-churn, high-LOC units** (vendored code, generated code, stable libraries) rarely deserve an agent; a short note in shared knowledge is enough.
- **Manifests in several places** (package.json plus pyproject.toml, an extension manifest plus a server) signal multiple runtimes, which are natural boundaries.

## 2. What to read beyond the script

- README, CONTRIBUTING, existing CLAUDE.md/AGENTS.md, any ADRs or `docs/`.
- CI workflows and Makefile/justfile/package scripts: these define "done" and become the shipper's gate.
- One entry point per runtime, and the module that wires components together.
- Tests layout and how tests are run.
- `git log --oneline -50` for the project's narrative and commit style.
- Grep for `TODO`, `HACK`, `XXX`, `do not`, `must`, `never`: these often mark invariants worth encoding.

## 3. Finding domain boundaries

Strong boundary signals (the more that apply, the clearer the domain):

- Different runtime or process (browser extension vs server vs CLI vs worker).
- Different language, build system, or test framework.
- Different trust boundary (handles credentials, PII, untrusted input, network egress, sandboxed execution).
- Different deploy or release path.
- Distinct vocabulary and data model.
- Own tests and own entry point.
- Changes cluster there independently of other units.

Weak signals (don't split on these alone): directory name, team folklore, file count.

Name domains after the *job* ("side-panel-ui", "agent-harness"), not after directories, so descriptions read naturally for routing.

## 4. Deciding the crew (the three tests)

A candidate domain becomes an agent only if it passes **all three**:

1. **Ownership.** You can write path globs that mostly belong to it. If you cannot say what it owns, it is a topic, not an agent.
2. **Knowledge density.** You can list several non-obvious facts (invariants, ordering constraints, gotchas, rationale, forbidden shortcuts) a fresh generalist would plausibly get wrong. If everything is obvious from reading the code, the agent adds nothing.
3. **Traffic or blast radius.** It is touched often, or a mistake there is expensive (security, data loss, release, public API).

Candidates that fail become:
- a section in a neighboring agent's knowledge file, or
- a shared knowledge file in `docs/crew/shared/` read by several agents (good for architecture, data flow, stack notes that cut across domains).

Cross-cutting roles (docs/decisions, shipper, reviewer, architect, security, QA, release) are judged with their own criteria in `core-roles.md`, using the same spirit: include only if the repo gives a reason.

Record, for each agent, which test evidence you relied on. It goes in the Crew Plan and in ROSTER.md, so a later audit can tell whether the reason still holds.

## 5. Sizing: typical outcomes, not limits

These describe what audits usually find; follow the evidence, not the table.

| Repo shape | Typical crew |
|---|---|
| Small single-purpose app or library | 1-2 owners, maybe a shipper |
| One app, several clear layers | 3-6 including docs/decisions and shipper |
| Multi-runtime product (extension + server + infra) | 6-9 |
| Regulated or security-sensitive product | add security/privacy as a first-class agent with review authority |
| Large monorepo with many services | 10+, usually organized by service plus the cross-cutting roles |

If the list feels long, re-check test 2 for each one. If it feels short for a sprawling repo, re-check test 3, since high-blast-radius areas deserve their own agent even with modest churn.

## 6. Split and merge triggers

**Split** an agent when: its knowledge file would exceed about 150 lines, it covers more than one runtime/language/trust boundary, or its description needs "and" twice to be accurate.

**Merge** two agents when: they co-change in more than about half of commits and share the same invariants, or one's knowledge file is mostly a pointer to the other's.

**Retire** an agent when its paths were deleted, or three consecutive audits found nothing non-obvious worth recording.
