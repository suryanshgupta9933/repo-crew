---
name: side-panel-ui
owner: side-panel-ui
covers:
  - extension/sidepanel/**
verified_at: 3fa91c2
---

# Side panel UI: knowledge

## Purpose and boundaries
Renders agent steps, tool results and errors for the user; sends user commands to the service worker. Does not execute tools or talk to the model.

## Map
- extension/sidepanel/App.tsx: root, subscribes to the message bus
- extension/sidepanel/state/: reducer for run state
- extension/sidepanel/components/: presentational components

## Invariants
- [code] Panel state is derived only from bus messages; it never reads tab content (extension/sidepanel/state/reducer.ts)
- [user] Errors shown to the user must be redacted summaries, never raw tool output
- [inferred] Streaming updates are throttled to ~10/s; confirm with the owner before changing

## Gotchas and rationale
- The panel is destroyed when closed; do not keep run state only in component memory (service worker owns it).

## Run, test, verify
- `npm test -- sidepanel` (source: package.json scripts)

## Decisions touching this area
- D-003

## Open questions
- Is the throttle value intentional?
