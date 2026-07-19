# Handoff — project bootstrap (design → repo setup)

Session date: 2026-07-18 → 2026-07-19. Session ran from `~/Users/gary` (parent dir); resume future sessions from the repo root instead.

### Active Task
Bootstrap the resume-tailor project: design analysis, decisions, and repo setup are done; next is implementation, starting with stage 1a (canonical schema + package scaffold). Success = working POC per the delivery order in `docs/tasks/PROGRESS.md`.

### Completed This Session
- Full design analysis produced and published as artifact https://claude.ai/code/artifact/c6a36252-1504-4337-a407-9649ce021d2d, mirrored to `docs/reference/resume-tailor-analysis.html` (keep both in sync; republish via the same scratchpad path or pass `url` from a new conversation).
- All 5 design questions decided (POC/product split) — recorded in the analysis doc's Decisions table and `docs/tasks/PROGRESS.md`.
- Repo created at `~/Web-Applications/resume-tailor`, git initialized on `main`, 4 commits (`be532d1` → `81a2600`).
- 11 workflow templates vendored from `~/.claude/shared/workflow/` into `.claude/commands/workflow/` with Python placeholder map + provenance headers.
- Consistency pass on design doc: intake-interview decision backported to case-1 diagram, truthfulness-guardrail row, and parser references (commit `c9c1529`).
- `docs/tasks/PROGRESS.md` created as single source of truth for state; `.claude/CLAUDE.md` and persistent memory (`~/.claude/projects/-Users-gary/memory/resume-tailor-app.md`) point to it.

### Next Steps
1. Stage 1a: freeze data contracts — canonical resume schema, fact inventory, job record, application log — then scaffold `src/resume_tailor/` (core library + Typer CLI shell), pytest, SQLite store.
2. Stage 1b: build the intake-interview flow (fact inventory first, then author the master resume; start the preference record).
3. In parallel any time: Track C spike — can Playwright fill a Greenhouse/Lever form with a dummy resume? (~2 days; outcome decides whether stage 4 is built.)
4. Full ordered list with later stages: `docs/tasks/PROGRESS.md`.

### Files Changed This Session
All in `~/Web-Applications/resume-tailor` (new repo):
- `README.md` — project overview + status
- `.claude/CLAUDE.md` — stack, commands, hard constraints, PROGRESS.md entry point
- `.claude/commands/workflow/*.md` — 11 vendored workflow commands
- `docs/reference/resume-tailor-analysis.html` — design analysis (artifact mirror)
- `docs/tasks/PROGRESS.md` — state tracker
- Outside repo: `~/.claude/projects/-Users-gary/memory/resume-tailor-app.md` + `MEMORY.md` index line

### Key Decisions & Context
- Phase 1 (interactive tailoring) is the prerequisite of phase 2 (automated pipeline): it produces the master resume, fact inventory, and preference record that phase 2 consumes.
- **Never reference `~/US/job seek/`** — user declared those files outdated and poorly written (2026-07-18, overriding an earlier pointer to the PDF there). POC authors a fresh master via intake interview; importers are product-stage only.
- Fact inventory is built at intake, BEFORE the master; master and all variants validate against it — no fabricated claims, ever.
- Submissions always behind batched user approval in POC; auto-apply is per-ATS and earned, never default.
- Core as a library, CLI as thin shell — productizing (web/mobile, multi-user, TW market) must be UI+accounts, not a rewrite.
- Variants keyed by job family (not per-JD) to prevent sprawl; fit scoring checks the whole library.
- Stack (user-confirmed): Python 3.12, Typer, anthropic SDK, Playwright, pytest, SQLite + markdown resume files.

### Known Issues / Blockers
- No code exists yet — nothing runnable.
- `debug.md` vendored command has `TODO(<PROJECT_BUG_PATTERNS>)` — fills in as real bugs appear.
- User must supply real resume facts during the stage-1b intake interview (user-only information).

### Test State
Not applicable — no code yet. Repo state verified: `git log` clean at `81a2600`, artifact/repo doc copies diff-identical.

### How to Resume
Open Claude Code in `~/Web-Applications/resume-tailor` (not the parent dir). Read `docs/tasks/PROGRESS.md` and this handoff, then start stage 1a: propose the canonical data contracts for user review, then scaffold the package. Design rationale, risk table, and decisions are all in `docs/reference/resume-tailor-analysis.html`.
