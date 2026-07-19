# resume-tailor

Resume tailoring + auto-apply POC. Design doc: `docs/reference/resume-tailor-analysis.html`.
**Start every session from `docs/tasks/PROGRESS.md`** (project state; update as items finish).

- Stack: Python 3.13 (`.venv`, Homebrew — no 3.12 on machine, `requires-python >=3.12`) — Typer CLI + core library; anthropic SDK; Playwright (apply engine); SQLite + markdown resume files
- Check: `.venv/bin/python -m compileall -q src` · Test all: `.venv/bin/python -m pytest` · Run: `.venv/bin/resume-tailor`
- Data contracts FROZEN 2026-07-19: `docs/reference/data-contracts.md` — change only with a dated note there.
- Layers: CLI command → core library (tailor engine · fit evaluator · apply engine) → stores (SQLite + resume files)

Hard constraints:
- Phase 1 authors the master resume via intake interview. Never import from `~/US/job seek/` (outdated, per user 2026-07-18). Exception 2026-07-19: repo-root `Hung-Ting_Lee_resume.pdf` is an approved seed reference — extract facts from it, but verify with the user before treating them as truth. PDF is git-ignored (PII).
- Truthfulness policy (user, 2026-07-19): goal is interviews, not documentary accuracy — actively calibrate exaggeration into the maximum-credible zone (impressive, never doubt-arousing). Background-checkable facts (employers, titles, dates, degrees) stay strictly verified; achievement metrics/framing may be `fidelity: plausible` (must fit org scale + role seniority, estimate-shaped numbers, improvisable backstory). Every claim still traces to a real fact in the inventory — that anchor blocks impossible claims.
- Submissions always behind batched user approval; auto-apply per-ATS, earned not default.
- Design core as a library, CLI as a thin shell (product stage wraps the same core in a web app).

Turn-end protocol (user, 2026-07-19): end every working turn with the 5-part report — **User blocked** · **Developing** · **Accomplished** · **Queue** · **Next** — per `~/.claude/skills/project-status/SKILL.md` (canonical definition). If nothing blocks, don't stop: continue with the next unblocked item in PROGRESS.md. Artifacts (status page, build map) update AUTOMATICALLY in the same turn as any state change they depict — never wait for the user to ask; stale artifacts are bugs. URLs in PROGRESS.md.

Plan-review principle (user, 2026-07-19): run the 8-question framework (`~/.claude/skills/plan-review`) before starting any new stage/wave and recurringly at boundaries; explain ELI5; publish the result as a "Direction check" section in the status artifact.

Commit at every completed, verified milestone (stage done, spike concluded, tests green) — don't accumulate days of work uncommitted. Push if a remote exists. (Lesson 2026-07-19: stages 1a–2 sat uncommitted for a full session.)

Workflow commands are vendored from `~/.claude/shared/workflow/`. Update via `/vendor-workflow update`.
