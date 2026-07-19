# resume-tailor

Resume tailoring + auto-apply POC. Design doc: `docs/reference/resume-tailor-analysis.html`.

- Stack: Python 3.12 — Typer CLI + core library; anthropic SDK; Playwright (apply engine); SQLite + markdown resume files
- Check: `python -m compileall -q src` · Test one: `pytest <file>` · Test all: `pytest` · Run: `python -m resume_tailor`
- Layers: CLI command → core library (tailor engine · fit evaluator · apply engine) → stores (SQLite + resume files)

Hard constraints:
- Phase 1 authors the master resume via intake interview. Never import from `~/US/job seek/` (outdated, per user 2026-07-18).
- Never fabricate resume facts — every variant claim must trace to the fact inventory.
- Submissions always behind batched user approval; auto-apply per-ATS, earned not default.
- Design core as a library, CLI as a thin shell (product stage wraps the same core in a web app).

Workflow commands are vendored from `~/.claude/shared/workflow/`. Update via `/vendor-workflow update`.
