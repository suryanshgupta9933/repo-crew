---
name: repo-crew
description: Audit a codebase and generate a crew of specialist Claude Code subagents for it, plus an orchestrator routing block in CLAUDE.md, committed per-domain knowledge files, a locked-decisions ledger, and a shipping gate (CI, PR, docs handoff). The audit decides how many agents the repo needs (2 or 12). Use this whenever the user says their project has outgrown the context window, the AI forgets or contradicts earlier decisions, context drift, or "one CLAUDE.md isn't enough"; wants to split a repo into agent teams, specialists, sub-teams or domain experts; wants subagents per module, an orchestrator, a decision log, or a shipping/release agent; or wants to audit, refresh, extend or fix an existing crew. Trigger even if they never say "skill" or "subagent".
license: MIT
compatibility: Requires git and Python 3.9+. The skill follows the Agent Skills standard and runs in Claude Code or any Agent Skills client; the agents it generates target .claude/agents/.
metadata:
  author: Suryansh Gupta
  version: "0.1.0"
---

# repo-crew

A solo dev (or small team) working with an AI assistant hits a ceiling as a repo grows: no single session can hold the whole codebase, earlier decisions get forgotten, and one giant CLAUDE.md either gets too long to follow or too vague to help. This skill fixes that structurally:

- **Specialist subagents**, each owning a slice of the repo and starting every task from a committed knowledge file, so expertise survives across sessions.
- **A thin orchestrator** (the main conversation) that only routes, using a short routing table in CLAUDE.md instead of reading everything.
- **A decision ledger** so locked decisions are looked up, not remembered.
- **A shipping gate** so CI, PRs and doc updates happen the same way every time.

The number and shape of agents comes from the audit of *this* repo. There is no fixed roster and no cap. A small repo may need two agents; a multi-runtime regulated product may need a dozen. Every agent must earn its place (see "Deciding the crew").

Why files, not memory alone: committed knowledge files are diffable, reviewable, shared by anyone cloning the repo, and can be checked for staleness by script. Claude Code's per-agent `memory:` field can be added on top, but never rely on it as the only store.

## Modes

**A crew is a repo-crew crew**: agents in `.claude/agents/` *plus* knowledge files in `docs/crew/` *plus* `docs/crew/ROSTER.md`. `docs/crew/ROSTER.md` is the marker.

| Mode | When | Go to |
|---|---|---|
| init | No `docs/crew/ROSTER.md` | Workflow below |
| audit | `docs/crew/ROSTER.md` exists; repo changed a lot; "do we have the right agents?" | `references/maintenance.md` |
| refresh | Knowledge may be stale | `references/maintenance.md` |
| add | Create/split/merge/retire one agent | `references/maintenance.md` |

Choosing the mode:

- If `docs/crew/ROSTER.md` does not exist, it is **init** — even if `.claude/agents/` already has files. Hand-written or third-party agents are not a crew.
- If `docs/crew/ROSTER.md` exists, it is **audit** unless the user says the knowledge is stale (**refresh**) or names one agent to change (**add**).
- When the request is explicit ("audit my agents"), honour the requested mode, but say which mode you picked and why in one line.

Existing `.claude/agents/` files in init mode are **inputs, not output**. Read them, reuse the ones that still pass the crew tests, and never overwrite or delete one without saying so in the plan. If a hand-written agent and a proposed agent cover the same paths, propose a merge rather than two agents competing.

## Ground rules

- **No user answering is not a stop.** When the plan or the interview needs an answer and none comes, proceed with the reasonable default, mark the affected facts `[inferred]`, and list them as open questions in the final report. The one exception is a conflict with a `locked` decision: that must halt and wait for the user.
- **Never commit or push** the target repo's changes unless asked.
- **Never edit the target repo's own source** — see "Write crew artifacts and nothing else" in step 4.

## Init workflow

### 1. Survey (read-only)

Run the survey script from the repo root, then read what the numbers can't tell you. Details in `references/survey.md`.

```bash
python <skill-path>/scripts/survey_repo.py . > /tmp/survey.md
```

Then read: README, existing CLAUDE.md/AGENTS.md, manifests, CI config, entry points, and one or two representative files per candidate domain. If your environment has subagents, dispatch one Explore-style subagent per candidate domain in parallel to draft its facts; otherwise read inline. Do not skim: wrong knowledge files are worse than none, because agents will trust them.

### 2. Decide the crew

Apply the tests in `references/survey.md` ("Deciding the crew") and the cross-cutting role criteria in `references/core-roles.md`. Present a **Crew Plan** to the user before writing anything:

- Table: agent name, one-line mission, owned paths (globs), tools profile, why it exists (which test it passed).
- "Considered and merged" list: candidate domains you folded into another agent or into shared knowledge, with the reason.
- Shared knowledge files you intend to create (architecture, data flow, stack notes).

Keep the plan short enough to read in two minutes. Let the user adjust, but don't pad it with questions.

### 3. Interview (one batch, only what the code can't tell you)

Ask in a single message, skipping anything already answerable from the repo:

1. Decisions already locked that agents must never reopen (and the reason, if they remember it).
2. The exact commands that must pass before merge, if CI config is missing or ambiguous; the branch/PR conventions.
3. Data or security rules that are hard constraints (regulated data, secrets, egress, licensing).
4. Which already-installed skills, plugins or MCP servers should be attached to which agents. Look in `.claude/skills/`, `~/.claude/skills/`, and installed plugins first, and offer what you find; use the user's own skill names (e.g. code-quality or reuse skills they rely on) rather than inventing any. If a named skill isn't installed, say so and omit it rather than referencing something that won't resolve.

If the user wants to proceed without answering, continue and mark the affected facts `[inferred]` (see "Truthfulness").

### 4. Generate

Create, never overwrite silently (if a file exists, show a diff or ask):

```
.claude/agents/<slug>.md          one per agent        (templates: references/agent-template.md)
docs/crew/<slug>.md               knowledge per agent  (frontmatter: covers, verified_at)
docs/crew/shared/<topic>.md       shared knowledge, if several agents need it
docs/crew/DECISIONS.md            decision ledger      (references/decisions.md)
docs/crew/ROSTER.md               who exists, owns what, last audit
docs/crew/routing-evals.md        routing test prompts (generated in step 5)
.crewignore                       globs for paths no agent owns on purpose
CLAUDE.md                         marker-delimited routing block (references/orchestrator-block.md)
```

**Write crew artifacts and nothing else.** You are creating a crew for a repo, not working on the repo. Do not edit the repo's source, tests, scripts, CI config or dependencies; do not run its build or test suite. If the survey turned up problems in the repo itself (a broken script, a failing test, a stale dependency), list them in the final report under "Repo problems found" and leave them alone. If the repo's only conventions file is `AGENTS.md` rather than `CLAUDE.md`, write the routing block into `AGENTS.md` instead.

Every path that no agent owns on purpose (generated code, vendored trees, throwaway demos, one-off scripts) goes in `.crewignore`, one glob per line. That keeps the drift check's uncovered-path report about real gaps instead of noise.

Rules that make the crew work:

- **Agent prompts stay short; knowledge lives in the knowledge file.** The prompt is paid for on every dispatch and is hard to keep current. The knowledge file is read on demand, edited by the owning agent, and checkable by script.
- **Agent `description` fields are the router.** Write them as "use when / not for" with concrete trigger words from the repo's own vocabulary, and make them a little pushy ("use proactively when..."), because under-triggering is the common failure.
- **Least privilege tools.** Reviewers and architects are read-only; only owners and the shipper get Edit/Bash. Note: if `memory: project` is used, the agent needs Write/Edit for its notes, and if its tools are an allowlist, include them.
- **Handoffs go through the orchestrator.** As far as I know subagents cannot spawn other subagents, so "shipper calls docs agent" is implemented as the shipper returning a structured `HANDOFF` block that the orchestrator dispatches. Verify against current Claude Code docs when generating, since this may change; if direct chaining becomes possible, keep the handoff block anyway for traceability.
- **Wire in skills the user named** inside the relevant agents' "Working rules" as explicit conditions ("before finishing any change, apply the X skill"), not as vague encouragement.

### 5. Verify routing

Generate `docs/crew/routing-evals.md`: 3 realistic user requests per agent, 3-5 cross-domain requests with the expected primary agent and handoffs, 2 requests that conflict with a locked decision, and 1-2 "ship it" requests. Then test: for each prompt, state which agent the orchestrator block would dispatch and why; for any miss, fix the agent `description` or the routing table, not the prompt. If subagents are available, additionally smoke-test each agent with a read-only question about its domain and confirm it opens its knowledge file and answers consistently with it. Details in `references/maintenance.md`.

### 6. Report

Tell the user what was created, what was marked `[inferred]` and needs their confirmation, which decisions are `proposed` vs `locked`, any repo problems you found but did not fix, and the one command to check drift later — using the absolute path to this skill's script, since it lives in the plugin, not in the target repo:

```bash
python3 <plugin-path>/skills/repo-crew/scripts/check_drift.py <target-repo>
```

Do not commit or push unless asked; suggest committing the crew in its own PR.

## Deciding the crew (summary)

A *domain* agent exists only if it passes all three: **ownership** (nameable path globs), **knowledge density** (several non-obvious invariants/gotchas a fresh generalist would likely get wrong), and **traffic or blast radius** (touched often, or costly when wrong). Failing candidates become sections in a neighbor's knowledge file or a shared knowledge file. Cross-cutting roles (docs keeper, shipper, reviewer, architect, security, QA, release) answer to the inclusion criteria in `references/core-roles.md` instead. Split an agent when its knowledge file outgrows ~150 lines or it straddles runtimes, languages or trust boundaries. Full criteria: `references/survey.md`.

## Truthfulness rules for knowledge files

Knowledge files are trusted by every future session, so errors compound.

- Tag each non-obvious fact `[code]` (verified by reading code, cite the path), `[user]` (stated by the user) or `[inferred]` (plausible, unverified). Surface all `[inferred]` items in the final report.
- Record only what a capable engineer would *not* quickly derive from reading the files: invariants, gotchas, rationale, boundaries, how to test/run, what not to touch. Do not paste code or restate the directory tree.
- Never promote an inferred decision to `locked`. Only the user locks decisions.
- Do not invent commands. If you could not find or run the test/CI command, say so in the file.

## Platform notes

Targets Claude Code (`.claude/agents/*.md`, CLAUDE.md). In a chat environment with no repo access, ask the user to run the survey script and paste its output (or the tree plus manifests), generate the files from that, and flag that nothing could be verified against code, so every fact is `[inferred]` or `[user]`.

## Reference files

- `references/survey.md`: survey interpretation, domain discovery, the crew tests, sizing.
- `references/core-roles.md`: cross-cutting roles (docs/decisions, shipper, reviewer, architect, security, QA, release) with inclusion criteria and specs.
- `references/agent-template.md`: agent file and knowledge file templates, description-writing guidance.
- `references/orchestrator-block.md`: CLAUDE.md block, dispatch rules, handoff and conflict protocol.
- `references/decisions.md`: ledger format and locking rules.
- `references/maintenance.md`: audit, refresh, add/split/merge/retire, routing evals.
- `scripts/survey_repo.py`: deterministic repo survey (units, churn, co-change, CI signals).
- `scripts/check_drift.py`: stale-knowledge and uncovered-path detector; also stamps `verified_at`.
