# Decisions

Index: D-001 One service worker owns run state [locked] | D-003 Panel never holds page content [locked] | D-007 Prefer SSE over websockets [proposed]

## D-003: Panel never holds page content or credentials
- status: locked
- date: 2026-09-12
- areas: side-panel-ui, security-privacy
- decision: The side panel renders redacted summaries only; raw page content stays in the worker.
- why: The panel is the least trusted surface (third-party UI libs, easier to screenshot or log).
- consequences: No tab content, cookies or tokens in panel state, props or logs.
- revisit if: never

## D-007: Prefer SSE over websockets for streaming
- status: proposed
- date: 2026-09-12
- areas: agent-harness
- decision: Stream model output to the UI via SSE.
- why: [inferred] simpler reconnects; seen in server/stream.py, not confirmed by the user.
- consequences: no bidirectional channel on the stream.
- revisit if: bidirectional control is needed.
