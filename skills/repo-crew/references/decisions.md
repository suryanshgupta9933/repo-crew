# Decision ledger

`docs/crew/DECISIONS.md` is the project's answer to "didn't we already decide this?". Agents look decisions up instead of remembering them, so the ledger must be short, scannable and trustworthy.

## Contents
- File format
- Statuses and who may set them
- Seeding the ledger
- How agents use it
- Keeping it healthy

## File format

Newest entries at the bottom. IDs are never reused.

```markdown
# Decisions

Index: D-001 <title> [locked] | D-002 <title> [proposed] | ...

## D-001: <short imperative title>
- status: locked | proposed | superseded by D-0NN
- date: YYYY-MM-DD
- areas: <agent slugs or paths this binds>
- decision: <one or two sentences, testable>
- why: <the reason; the part that gets lost first>
- consequences: <what this forbids or requires>
- revisit if: <condition under which reopening is legitimate, or "never">
```

Keep each entry to about 8 lines. Link to longer discussion elsewhere instead of pasting it.

## Statuses and who may set them

- **locked**: the user said so, explicitly, or confirmed a proposal. Agents must not contradict it or work around it.
- **proposed**: evidenced in code, README or an agent's analysis, but not confirmed by the user. Agents treat it as strong guidance and may raise a question about it.
- **superseded**: replaced by a newer decision; keep the entry and link forward so history is not lost.

Only the user locks, unlocks or supersedes. An agent that thinks a decision is wrong writes `decisions-needed` in its handoff with the argument; it does not edit the ledger status itself, and it keeps following the locked decision until told otherwise.

## Seeding the ledger

During init:
1. Add everything the user stated in the interview as `locked`, with their reason if given.
2. Add decisions evident in code or docs (framework choices, architectural patterns, explicit "we chose X because" comments, existing ADRs) as `proposed`. Cite where you saw them.
3. Show the user the `proposed` list in the final report and invite them to lock, reject, or edit.

If the repo already has ADRs, import by reference (link or copy the essentials with the original ID in the title) rather than rewriting history.

## How agents use it

At the start of a task an agent scans the index and reads entries whose `areas` match its work. A request that conflicts with a locked entry results in a `needs-decision` handoff naming the D-ID, not a silent deviation and not a refusal without explanation.

The docs-and-decisions keeper appends new entries only when the user states or confirms a decision during the work (it can be reported via a handoff's `knowledge-updates`).

## Keeping it healthy

- One decision per entry; if an entry needs "and", split it.
- Prefer decisions that are testable ("all outbound requests go through X") over vague values ("keep it simple").
- During audits, check that every locked decision is still true in code. A locked decision that the code violates is either a bug to fix or a decision to supersede; report it to the user either way.
