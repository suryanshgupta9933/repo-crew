# Orchestrator block for CLAUDE.md

The main conversation is the orchestrator. It should route and integrate, not read the whole repo. Insert the block below into CLAUDE.md between markers so later audits can update it idempotently. If CLAUDE.md is missing, create it with just this block plus a one-paragraph project summary taken from the README.

Keep the block under ~50 lines; the roster and knowledge files hold the detail.

## Block template

```markdown
<!-- repo-crew:start -->
## Crew protocol

This repo has specialist subagents in `.claude/agents/`. Route work to them
instead of reading large parts of the codebase yourself.

| Agent | Dispatch for | Owns |
|---|---|---|
| <slug> | <one-line trigger> | <main globs> |
| ... | ... | ... |

Details: `docs/crew/ROSTER.md`. Locked decisions: `docs/crew/DECISIONS.md`.

### Dispatch rules
1. For any task touching code, pick the owning agent from the table. If the
   task spans domains, dispatch the architect/planner first (if present),
   otherwise sequence owners yourself, passing contracts between them.
2. Before dispatching a change that might contradict a locked decision, check
   DECISIONS.md yourself and tell the agent which D-IDs apply.
3. Independent tasks in different domains can run in parallel; tasks sharing
   files or contracts must run in sequence.
4. Never edit inside an agent's `covers` paths yourself except for trivial
   one-line fixes; dispatch the owner.

### Handoffs
Subagents cannot dispatch each other. Each agent ends with a block:

    HANDOFF
    status: done | blocked | needs-decision
    changed: <files>
    next:
      - agent: <slug>   reason: <why>   input: <what to pass>
    knowledge-updates: <facts the docs keeper should record, or "none">
    decisions-needed: <questions only the user can answer, or "none">

The orchestrator dispatches every `next` item, relays `decisions-needed` to the
user, and never drops a handoff silently.

### Ship path
Work finishes through the shipper: feature branch, full local CI gate, PR, then
the docs-and-decisions keeper. Do not merge unless the user asks.

### Conflicts and locked decisions
If an agent reports a conflict with a locked decision, stop and ask the user.
Only the user can lock, unlock or supersede a decision.
<!-- repo-crew:end -->
```

Adapt wording to the actual roster: if there is no shipper or architect, delete those lines rather than leaving dangling references.

## Updating the block

Replace everything between the markers; never touch content outside them. Re-render the table from `ROSTER.md` so the two cannot disagree.

## ROSTER.md format

```markdown
# Crew roster
Last audit: <date> at <short sha>

| Agent | Mission | Covers | Why it exists | Knowledge | Verified |
|---|---|---|---|---|---|
| <slug> | ... | globs | ownership / density / traffic evidence | docs/crew/<slug>.md | <sha> |

## Shared knowledge
- docs/crew/shared/<topic>.md: <used by which agents>

## Considered and merged
- <candidate>: <folded into X because ...>
```
