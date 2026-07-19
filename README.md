# resume-tailor

Resume tailoring + job-application assistant. POC stage: personal, CLI/agent-driven, US job market.

Two phases sharing one engine:

- **Phase 1 — interactive tailoring**: intake interview → fact inventory → master resume + preference record. Prerequisite for everything else.
- **Phase 2 — automated pipeline**: job sourcing → fit scoring against the whole resume library → auto-tailoring (truth-bounded) → apply engine (batched approval; blocked forms go to a manual queue).

Full design analysis with diagrams: [`docs/reference/resume-tailor-analysis.html`](docs/reference/resume-tailor-analysis.html)
(live artifact: <https://claude.ai/code/artifact/c6a36252-1504-4337-a407-9649ce021d2d>)

## Status

Design settled 2026-07-18. No code yet — next steps: freeze the canonical resume schema, scaffold core-as-library + CLI shell, run the phase-1 intake interview.
