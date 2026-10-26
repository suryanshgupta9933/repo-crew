# Agent and knowledge file templates

## Contents
- Agent file template
- Writing the `description` (the router)
- Knowledge file template
- Shared knowledge file template
- What belongs in a knowledge file
- Optional: `memory:` field

## Agent file template

Save as `.claude/agents/<slug>.md`. Keep the body under ~60 lines; push detail into the knowledge file.

`<slug>` is lowercase kebab-case naming the domain, without a project-name prefix: `backend-api`, `panel-ui`, `data-db`. One crew per repo means the project name is already implied. The slug is the agent's identity: the file name, the `name:` field, the knowledge file `docs/crew/<slug>.md` and every reference to it in the roster, ledger and routing table must all match exactly.

```markdown
---
name: <slug>
description: <Use proactively when ... . Owns ... . Not for ... (see <other-agent>).>
tools: Read, Grep, Glob, Edit, Write, Bash
model: inherit
---

You are the <domain> specialist for <project>. You own: <globs>.
You do not own: <adjacent areas and which agent does>.

## Start every task
1. Read `docs/crew/<slug>.md` fully. It is your long-term memory.
2. Read any `docs/crew/shared/*.md` it links to that the task touches.
3. Scan `docs/crew/DECISIONS.md` for locked entries tagged with your area.
4. Run `git log --oneline -10 -- <your globs>` to see recent changes. If
   `git log -1 <verified_at>` predates changes to your globs, say so in your
   report.

## Working rules
- <3-6 rules specific to this domain; the invariants that matter most.>
- Reuse existing components/utilities before writing new ones; search first.
- <If the user named skills: "Before finishing any change, apply the <skill> skill.">
- If a request conflicts with a locked decision, stop and report; never work around it.

## Before you report
- If your change alters an invariant, boundary, command or gotcha, update
  `docs/crew/<slug>.md` (and keep `covers` accurate).
- End with a HANDOFF block (format in CLAUDE.md "Crew protocol").
```

Fields: `name` and `description` are required by Claude Code; `tools`, `model`, and `memory` are optional. Check the current Claude Code subagent docs before using newer fields.

## Writing the `description` (the router)

The orchestrator picks agents mainly from this one field, so it carries the routing quality of the whole crew.

Include, in this order:
1. **When**: "Use proactively when ..." with concrete triggers in the repo's own vocabulary (file names, feature names, error types), not abstractions.
2. **Owns**: the domain in one clause.
3. **Not for**: the nearest confusable domain and which agent handles it. This is what prevents misroutes between neighbors.

Weak: "Handles UI stuff."
Strong: "Use proactively for any change to the side panel (React components, panel state, message passing from the service worker, extension CSS). Owns everything under extension/sidepanel/. Not for the agent loop or tool execution (see agent-harness) or manifest/permissions changes (see security-privacy)."

Be a little pushy: under-triggering is the usual failure.

## Knowledge file template

Save as `docs/crew/<slug>.md`.

```markdown
---
name: <slug>
owner: <slug>
covers:
  - <glob>/**
  - <glob>
verified_at: <git short sha at time of writing>
---

# <Domain>: knowledge

## Purpose and boundaries
<2-4 lines: what this domain does, what it does not, where it hands off.>
Owns: <the globs above, in words>. Not for: <adjacent areas and which agent does>.

## Map
<Key entry points and files with one-line roles. Not a full tree.>

## Invariants (break these and things fail)
- [code] <invariant> (<path>)
- [user] <invariant the user stated>
- [inferred] <plausible, unverified; needs confirmation>

## Gotchas and rationale
- <non-obvious thing, and why it is that way>

## Contracts with other domains
- <interface/message/schema this domain depends on or exposes; link shared note>

## Run, test, verify
- <exact commands and their source; or "not found / not run">

## Decisions touching this area
- <D-IDs from DECISIONS.md>

## Open questions
- <things the next session should confirm>
```

## Shared knowledge file template

Save as `docs/crew/shared/<topic>.md`. Shared notes carry `verified_at` but **no `covers`** — they are not a path owner, so the drift checker only tracks their freshness.

```markdown
---
name: <topic>
owner: <slug of the agent that maintains it>
verified_at: <git short sha at time of writing>
---

# <Topic>

<The cross-cutting fact: architecture, data flow, stack, shared vocabulary.>
```

## What belongs in a knowledge file
Include: invariants, ordering/timing constraints, gotchas that already bit someone, rationale for non-obvious choices, contracts with other domains, exact verify commands, "do not touch" zones.

Exclude: code listings, full directory trees, anything obvious from a quick read, vague aspirations ("keep code clean"), duplicated content already in shared notes (link instead).

Target 60-150 lines. If it grows past that, apply the split trigger in `survey.md`.

## Optional: `memory:` field

Claude Code can give a subagent its own notebook directory via `memory: project` in frontmatter, shared through git, or `user` for cross-project learnings. It can complement the knowledge file for agent-written observations, but:
- it only loads the start of the notebook's index, so it is no substitute for a curated knowledge file;
- it depends on auto memory being enabled and has had reports of not working when a `tools` allowlist excludes Write/Edit;
- keep project facts in `docs/crew/` so they are reviewed like code.

Use it only if the user wants it, and say so in the report.
