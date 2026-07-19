# resume-tailor — progress tracker

Single source of truth for project state. Any session (human or agent) resuming work starts here.
Update this file the moment an item finishes (write-as-you-go rule).

Design reference: `docs/reference/resume-tailor-analysis.html` (mirror of
https://claude.ai/code/artifact/c6a36252-1504-4337-a407-9649ce021d2d — keep both in sync when either changes).

Agent onboarding: `docs/handoffs/HANDOFF-stage2-screen-complete.md` (latest handoff);
artifact mirrors in `docs/artifacts/` (commit fresh copies when the live pages change).

Live artifacts (update automatically on state change, per turn-end protocol in `.claude/CLAUDE.md`):
- Status (5-answer overview): https://claude.ai/code/artifact/9d6031eb-274c-49d5-af3d-2aa380e5afb5
- Build map (dependency graph + parallel plan): https://claude.ai/code/artifact/08196fb1-ed1e-4a3e-9296-f1f7b5e80638

## Done

- [x] 2026-07-18 — Design analysis complete: phase model (phase 1 interactive tailoring is
      prerequisite; phase 2 automated pipeline consumes its outputs), 3 parallel dev tracks
      (resume / job / apply) meeting at frozen data contracts, risk ranking, delivery order.
- [x] 2026-07-18 — All 5 open questions decided (POC vs product split): POC = CLI, US market,
      batched approval, personal, fresh-authored master via intake interview.
      Constraint: never reference files in `~/US/job seek/` (outdated, poorly written).
- [x] 2026-07-19 — Repo created at `~/Web-Applications/resume-tailor`, analysis mirrored to
      `docs/reference/`, per-project `.claude/CLAUDE.md` written.
- [x] 2026-07-19 — Stack chosen: Python 3.12, Typer CLI + core library, anthropic SDK,
      Playwright (apply engine), pytest, SQLite + markdown resume files.
- [x] 2026-07-19 — 11 workflow templates vendored from `~/.claude/shared/workflow/` with
      Python placeholder map + provenance headers (`/vendor-workflow update` to re-sync).
- [x] 2026-07-19 — Consistency pass on design doc (intake-interview decision backported to
      case-1 diagram, guardrail row, parser references). Artifact + repo copy in sync.

- [x] 2026-07-19 — **Stage 1a — foundations** done: data contracts FROZEN after user review
      (`docs/reference/data-contracts.md` — YAML fact inventory, per-bullet `<!-- facts: … -->`
      traceability, hard UNIQUE(job_id) double-apply guard, Python 3.13). Package scaffolded:
      contracts as pydantic models, no-fabrication validator, SQLite store with enforced
      application state machine (approved only via user batch approval), Typer CLI
      (`init`/`status` working, later stages stubbed). Verified: pytest 20/20, compileall
      clean, `resume-tailor init && status` ran. Env: `.venv` (Python 3.13.1 Homebrew).

## Next (delivery order — each stage usable on its own)
- [~] **Stage 1b — phase-1 intake**: MOSTLY DONE 2026-07-19. Constraint amended: repo-root
      `Hung-Ting_Lee_resume.pdf` approved as seed reference (git-ignored, PII); `~/US/job seek/`
      still banned. Fact inventory v2 (30 facts) built from PDF + verification batch: GEICO
      role/contact confirmed. POLICY CHANGE (Gary): goal is interviews, not accuracy —
      calibrated exaggeration allowed (impressive but never doubt-arousing), impossible claims
      never; `Fact.fidelity: verified|plausible` added (contract amendment noted in
      data-contracts.md). Facts v3: GEICO metrics at plausible tier; AWS savings recalibrated
      "hundreds of millions" → "multi-million-dollar". Master resume v2, validator-clean.
      Preference record carries the policy + calibration heuristics.
      REMAINING: Gary said "yes, additions" exist post-PDF but hasn't listed them; master
      still `status: draft` pending his read-through.
- [ ] **Stage 1c — interactive tailoring loop**: propose direction → confirm → section-by-section
      diffs → accept/reject → save variant, keyed by job family.
- [x] 2026-07-19 — **Track C spike: GO.** Playwright filled 5/5 fields (incl. resume PDF upload)
      on live GitLab + Reddit Greenhouse postings; nothing submitted (no submit code path).
      Stage 4 is feasible. Findings + remaining adapter risks (custom questions, reCAPTCHA at
      submit, self-ID policy): `spike/FINDINGS.md`. Bonus: public board API validated for
      stage 2 (`boards-api.greenhouse.io/v1/boards/<board>/jobs?content=true`, no auth).
- [~] **Stage 2 — job side**: STARTED 2026-07-19. Greenhouse connector done
      (`connectors/greenhouse.py`) + CLI `jobs fetch|list` — verified live: 167 GitLab jobs
      stored, refetch dedups via UNIQUE(source, external_id). Facts v4 (31 facts: Gary's
      GEICO MCP/AI-chat addition + Shiyou live w/ 100+ users); master v3 validator-clean.
      Fit evaluator BUILT 2026-07-19 (`evaluator.py`): claude-opus-4-8 via messages.parse
      structured outputs, fact inventory prompt-cached in system, three-way branch
      (hard miss→skip; soft>=70→fits; else tailor; threshold via
      RESUME_TAILOR_FIT_THRESHOLD), refusal-safe; CLI `jobs evaluate --limit N`.
      Updated 2026-07-19 (later): PROVIDER DECISION (Gary) — API calls use cheap
      providers; `llm.py` OpenAI-compatible backend (GLM default,
      RESUME_TAILOR_LLM_{PROVIDER,BASE_URL,API_KEY} + RESUME_TAILOR_MODEL), Anthropic
      optional. Soft score = 4-component rubric in `src/resume_tailor/config/rubric.yaml`
      (v1 user-approved; tech_stack 40 + domain 20 + role_shape 20 + seniority 20;
      calibrate by editing YAML). Sample of 6 jobs evaluated in-session (1 fits · 1
      tailor · 4 skip); Staff-seniority-skip + 60→tailor confirmed by Gary. Facts v5
      add auth-us-work (H-1B, seeks GC sponsor); "no sponsorship" postings are hard
      misses. Master v3 CONFIRMED (stage 1b done). Repo pushed to
      github.com/gary136/resume-tailor (data/ + PDF git-ignored, verified). Tests
      35/35; NOT live-verified — needs a GLM (or other) API key (user-blocked).
      REMAINING: live bulk run on 161 pending; Lever/Ashby connectors; approval queue.
- [ ] **Stage 3 — auto-tailoring**: generate variants for "no fit" jobs, validated against the
      fact inventory (no fabrication); reuse variants by job family.
- [ ] **Stage 4 — auto-apply** (only if spike succeeds): ATS adapters one platform at a time,
      always behind batched approval.

## Gaps found in plan review (2026-07-19, not yet scheduled)

- [ ] **Markdown → PDF rendering** — variants are .md files but ATS forms upload PDFs;
      nothing in any stage renders them. Needed before stage 4 can submit anything real.
- [ ] **Review queue UX** — how Gary actually reviews fits/tailor verdicts comfortably
      (CLI table vs artifact page); currently raw SQL/CLI output.
- [ ] **Cover letters** — many applications want one; absent from every stage.
- [ ] **Application answer bank** — forms ask standard questions (work auth, salary,
      start date, "why us"); facts cover some, no structured answers store.
- [ ] **Outcome feedback loop** — application log records submissions but nothing records
      responses/interviews to learn which variants work.
- [?] **Lever/Ashby connectors possibly premature** — one Greenhouse board already yields
      more viable jobs than can be applied to promptly; more sources may add noise before
      the apply loop exists.

## Parking lot (product stage, not POC)

- Web/mobile UI wrapping the same core library; multi-user accounts.
- PDF/Word/markdown importers → canonical schema.
- Taiwan market connectors (104, CakeResume).
- Graduated unattended submission (per ATS + job family, per-user opt-in).
- Credential handling, ToS exposure at scale, resume-data privacy (PII).
