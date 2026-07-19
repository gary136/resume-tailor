# Handoff — stage 2 screen complete (2026-07-19)

For any agent (or human) continuing this project with zero conversation context.
Read order: this file → `docs/tasks/PROGRESS.md` → `.claude/CLAUDE.md` → the two
artifact mirrors in `docs/artifacts/` (status.html = fast state, build-map.html =
plan + dependencies; live versions at the URLs in PROGRESS.md — republish via the
Artifact tool's `url:` parameter to keep those URLs stable).

### Active Task
Personal resume-tailoring + auto-apply POC for Gary (Hung-Ting Lee). Goal: interviews
with a fraction of the manual effort — machine sources jobs, triages them, tailors
resumes credibly, applies behind batched approval. Phase 1 (facts, master resume,
preferences) is DONE; phase 2 (automated pipeline) is half-built and proven end-to-end
on one real board.

### Current State (matches docs/artifacts/status.html)
- **167 GitLab jobs screened: 1 fits (AI Engineer, soft 78) · 1 tailor (SRE Cloud
  Cost, soft 60) · 165 skip.** Screen ran through the three-tier funnel: free
  prefilter (search profile) → GLM rubric scoring → Gary.
- Master resume confirmed by Gary; renders to ATS-ready PDF (`resume-tailor render master`).
- Playwright spike passed: auto-apply (stage 4) is feasible; nothing is ever submitted
  yet, and never without batched approval.
- Tests 54/54 (`.venv/bin/python -m pytest`). All work committed and pushed.

### How to Run
- Python 3.13 venv at `.venv`; CLI `.venv/bin/resume-tailor` (init · status · render ·
  jobs fetch/prefilter/list/evaluate).
- LLM: GLM free tier via OpenAI-compatible backend (`src/resume_tailor/llm.py`).
  Key lives in git-ignored `data/.env` (`RESUME_TAILOR_LLM_API_KEY`); export it before
  `jobs evaluate`. Model `glm-4.5-flash`; ~80s/job (thinking model), 300s timeout,
  per-job error isolation (failures stay pending; just re-run).
- User-owned config: `data/search_profile.yaml` (or packaged default —
  keywords/locations/sponsorship phrases/target boards) and
  `src/resume_tailor/config/rubric.yaml` (soft-score rubric v1, threshold 70).

### Where Everything Lives
- `src/resume_tailor/` — contracts.py (frozen data contracts) · validation.py
  (no-fabrication: every resume bullet needs `<!-- facts: id -->` refs) · store/ ·
  connectors/greenhouse.py · prefilter.py · evaluator.py · llm.py · render.py · cli.py
- `data/` (git-ignored, PII — exists only on Gary's machine): facts.yaml (v5, 32 facts),
  resumes/master.md + master.pdf, preferences.yaml, search_profile.yaml override,
  resume_tailor.db, .env
- `docs/reference/data-contracts.md` — FROZEN contracts; change only with a dated note.
- `spike/` — Playwright/Greenhouse form-fill spike (GO) + FINDINGS.md.

### Non-Negotiable Protocols (full text in .claude/CLAUDE.md)
1. **Truthfulness**: calibrated exaggeration allowed (impressive, never doubt-arousing);
   background-checkable facts (employers/titles/dates/degrees/work-auth) strictly
   verified; every claim traces to a fact in the inventory. Gary is H-1B seeking
   green-card sponsorship — "no sponsorship"/"citizens only" postings are hard skips.
2. **Approval gate**: nothing is ever submitted without Gary's explicit batch approval;
   the DB state machine enforces it (`approved` only via approve_batch).
3. **Turn-end protocol**: 5-part report (User blocked · Developing · Accomplished ·
   Queue · Next); continue autonomously while unblocked; artifacts update automatically
   in the same turn as state changes (`~/.claude/skills/project-status`).
4. **Plan review**: 8-question framework before new stages and at wave boundaries,
   ELI5, results → "Direction check" in status artifact (`~/.claude/skills/plan-review`).
5. **Commit at every verified milestone; push (origin = github.com/gary136/resume-tailor).**

### Next Steps (all currently gated on Gary)
1. AI Engineer (fits): apply decision — submission is manual until stage 4.
2. SRE Cloud Cost (tailor): first stage-1c interactive tailoring session → variant.
3. Sourcing growth: Gary names target companies → add board slugs to search profile,
   rerun fetch → prefilter → evaluate.
4. Remaining plan-review gaps in order: review-queue UX · answer bank · cover letters ·
   outcome feedback loop. (Lever/Ashby connectors deliberately deprioritized.)
5. Wave-2→3 boundary = run the plan review again before building stage 3.

### Known Issues / Pitfalls
- GLM sometimes exceeds even 300s (one job needed in-session evaluation). Retry or
  evaluate in-session; jobs left pending are safe.
- Rubric sub-scores aren't persisted (only the total) — small schema improvement waiting.
- Prefilter exclude keywords are blunt (`staff` rejects "Intermediate to Senior Staff"
  ranges) — acceptable, user-editable.
- The GLM API key passed through chat once; rotating it on the GLM console is cheap
  insurance. Never commit data/.env.

### Test State
54/54 passing (contracts, validation, store state machine, connector, evaluator+rubric,
LLM backend incl. JSON-repair, prefilter incl. Austria/US regression, render).
