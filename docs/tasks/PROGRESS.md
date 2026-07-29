# resume-tailor — progress tracker

Single source of truth for project state. Any session (human or agent) resuming work starts here.
Update this file the moment an item finishes (write-as-you-go rule).

Design reference: `docs/reference/resume-tailor-analysis.html` (mirror of
https://claude.ai/code/artifact/c6a36252-1504-4337-a407-9649ce021d2d — keep both in sync when either changes).

Live artifacts (update at end of every working session, per turn-end protocol in `.claude/CLAUDE.md`):
- Status (5-answer overview): https://claude.ai/code/artifact/9d6031eb-274c-49d5-af3d-2aa380e5afb5
- Build map (dependency graph + parallel plan): https://claude.ai/code/artifact/08196fb1-ed1e-4a3e-9296-f1f7b5e80638

## Wave 3 log

- [x] 2026-07-28 — **CAPTCHA-at-submit test: DECISIVE.** Built a CAPTCHA *detector*
      (recon only — NEVER a solver/bypass; defeating CAPTCHA is anti-abuse circumvention,
      out of scope by policy). Live on the real GitLab form it found **invisible reCAPTCHA
      Enterprise** (score-based; `.grecaptcha-badge` + `___grecaptcha_cfg` + enterprise.js).
      CONCLUSION → the last big architecture question is settled: fully-unattended
      auto-submit is NOT viable on reCAPTCHA-protected ATSs (a headless bot submit gets
      flagged/blocked/down-scored). **Stage 4 is ASSISTED-SUBMIT, not auto-submit:** the
      machine prepares the complete application (resume + fields + truthful answers), and
      the HUMAN reviews and presses submit in a real browser session (handling any
      human-verification). This is also the ethical/ToS-respecting design. Detector wired
      into the rehearsal report; 100 tests.
- [x] 2026-07-28 — **Cover letters DROPPED from scope** (user: most companies don't require
      one). Removed from the remaining sequence.

- [~] 2026-07-27 — **Custom-question answering (door A)**. Answer ENGINE built + truth-table
      verified (94 tests): work-authorization questions answered DETERMINISTICALLY & truthfully
      from auth-us-work (sponsorship→Yes; "without sponsorship"→No; citizenship→No; ambiguous
      work-auth→FLAG for human, never guessed), softer questions from the answer bank, unknowns
      left blank. Question EXTRACTION works (all 14 GitLab questions found + paired). Browser
      FILLING is PARTIAL: native controls + some react-select fill; GitLab's custom react-select
      widgets are inconsistent to drive (aria-controls scoping fixed the phone-widget option
      bleed; still only some fill). SAFE failure mode: unfilled = blank for the human, NEVER a
      wrong answer — which fits the never-auto-submit + human-approval design. REMAINING: robust
      react-select driving per widget; answer-bank fields for country-of-residence / employment-
      restrictions if desired.

- [x] 2026-07-27 — **Practice applier built (stage 4, DEV-MODE)**. `apply/` package fills
      real Greenhouse forms from the applicant profile (identity parsed from the contact
      fact) + the one-page resume PDF, screenshots the result, and NEVER submits (no submit
      code path; guarded by a test). CLI `apply-practice <job_id>` auto-picks the tailored
      variant or master. LIVE-VERIFIED on the real GitLab AI Engineer form: 5/5 core fields
      + resume filled, nothing submitted, screenshot confirmed. 83 tests. REMAINING stage-4
      work (seen in the screenshot): per-company custom questions (work-auth / why-us /
      sponsorship dropdowns) mapped from the answer bank; reCAPTCHA behavior at submit.

- [x] 2026-07-27 — **One-page resumes by default** (user request). Render tightened to a
      dense ATS-safe stylesheet (fits the full 26-bullet master on one page, ZERO content
      dropped) with an auto-trim fallback (top-N bullets/role, floor 3, .md untouched) if a
      resume still overflows. Tailoring engine now targets one page at draft time. Honest
      framing recorded: one page helps the human reader, NOT the ATS parser. Guide:
      `docs/reference/resume-style-guide.md`; rule in CLAUDE.md + preferences. `render`
      defaults to one page (`--full` opts out). pypdf added for page counting. 79 tests.

- [x] 2026-07-26 — **More job sources + smarter filter** (user request). Built Ashby and
      Lever connectors (mirror the Greenhouse one) behind a source dispatcher +
      `jobs fetch-all`. Ashby unlocks Plaid + Ramp (233 real postings; both had moved off
      Greenhouse). Widened title keywords (architect, swe, full-stack, software, applied
      scientist, …) and hardened the free filter from LIVE data: whole-word excludes,
      seniority level-range rescue ("Intermediate to Senior Staff" survives), excluded
      sales-engineering "Solutions Architect" roles, and a foreign-location block so US
      cities ("New York, NY") stop being wrongly rejected. Search profile v2, 75 tests.
      LinkedIn/Indeed deliberately not built (no clean API; ToS-hostile scraping) — more
      ATS boards are the legitimate breadth path. NOTE: 338 jobs now sit pending (survived
      the free filter across 6+ boards) — a scoring run is a deliberate choice, not auto.

- [x] 2026-07-26 — **First variant CONFIRMED** (`sre-cloud-cost`, PDF rendered). Engine
      built + live-hardened (fence tolerance, completeness gate, output budget). Division
      of labor learned: cheap models hold STRUCTURAL rules, not SEMANTIC ones — tailoring
      drafts are judgment-tier work (in-session Claude / stronger model), engine handles
      scale + gates. Accept-rate ledger: machine drafts 0/2 · judgment-tier 1/1 (one
      phrasing edit: daily cloud = Azure ONLY, never AWS). Facts v7, rubric v3, emphasis
      ranking: distributed systems > full-stack > AI harness > large-scale data > cloud.

- [x] 2026-07-26 — **Answer bank built** (`AnswerBank` contract + `data/answers.yaml`
      with Gary's answers: base $140–180k / total $170–250k; start flexible; remote or
      NYC ≤3 days in person; why-company = ownership+depth seed, adapted per company at
      judgment tier). Consumed by the stage-4 adapter next.

## Plan amendments (plan review 2026-07-26 — user-driven recalibration)

- **Build focus, not hunt focus**: purpose is BUILDING the auto-tailor/apply system;
  real job queues are TEST FIXTURES until Gary flips apply-mode on. (Drift caught & fixed.)
- **Stage 1c absorbed into stage 3**: machine drafts variants (stage 3 engine), Gary
  accept/rejects diffs — that review IS the 1c preference collection. No separate 1c build.
- **Revised remaining sequence**: stage 3 auto-tailor engine → answer bank → stage 4
  adapter in dev-mode (fills forms against dummy data, NEVER submits) → cover letters →
  outcome feedback loop → only then apply-mode, per Gary.
- **Experience calibration (facts v6, rubric v2)**: full-stack > AI harness > cloud
  (user-level, Azure/AWS); never pitch infra-engineer identity.
- **Sourcing wave 2 recorded**: 5 Greenhouse boards fetched (2,104 jobs), 24 survivors,
  7 scored (5 fits total · 1 tailor), 17 parked pending — fixtures, not harvest.
  NOTE (fresh-review finding): the 7 wave-2 verdicts have run-evidence but no Gary
  spot-check yet — sample them during wave-3 fixture use.

## Immediate next (as of 2026-07-19 end of session — all three user-gated)

1. **Apply decision — AI Engineer @ GitLab** (fits, soft 78): master.pdf is ready
   (`resume-tailor render master`); submission is manual until stage 4.
2. **First tailoring session — SRE Cloud Cost @ GitLab** (tailor, soft 60): stage 1c,
   interactive with Gary; creates the `sre-cloud-cost` variant.
3. **Sourcing growth**: Gary names target companies → add Greenhouse slugs to
   `data/search_profile.yaml` → `jobs fetch <slug>` → `jobs prefilter` → `jobs evaluate`.

Runtime notes for a fresh agent: GLM key in git-ignored `data/.env`
(`export RESUME_TAILOR_LLM_API_KEY=$(cut -d= -f2 data/.env)`); model glm-4.5-flash
(free tier, ~80s/job, occasional >300s timeouts — failed jobs stay pending, re-run);
protocols (turn-end report, artifact auto-update, plan-review principle, truthfulness
policy, commit-at-milestone) in `.claude/CLAUDE.md`; artifact URLs above — republish
same file path in the owning conversation, or pass `url:` from a new one.

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
- [x] **Stage 1b — phase-1 intake**: DONE 2026-07-19 (master CONFIRMED; facts v5 incl. additions + auth-us-work). Constraint amended: repo-root
      `Hung-Ting_Lee_resume.pdf` approved as seed reference (git-ignored, PII); `~/US/job seek/`
      still banned. Fact inventory v2 (30 facts) built from PDF + verification batch: GEICO
      role/contact confirmed. POLICY CHANGE (Gary): goal is interviews, not accuracy —
      calibrated exaggeration allowed (impressive but never doubt-arousing), impossible claims
      never; `Fact.fidelity: verified|plausible` added (contract amendment noted in
      data-contracts.md). Facts v3: GEICO metrics at plausible tier; AWS savings recalibrated
      "hundreds of millions" → "multi-million-dollar". Master resume v2, validator-clean.
      Preference record carries the policy + calibration heuristics.
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
      github.com/gary136/resume-tailor (data/ + PDF git-ignored, verified).
      SCREEN COMPLETE 2026-07-19 (late): tier-0 prefilter added (search_profile.yaml —
      title/location/sponsorship/citizenship phrases; 123 rejected free, Austria/US
      word-boundary bug caught+tested) → GLM scored survivors → ALL 167 triaged:
      1 fits (AI Engineer 78) · 1 tailor (SRE Cloud Cost 60) · 165 skip. Tests 54/54.
      REMAINING: review-queue UX; approval queue; more boards when Gary names targets.
- [ ] **Stage 3 — auto-tailoring**: generate variants for "no fit" jobs, validated against the
      fact inventory (no fabrication); reuse variants by job family.
- [ ] **Stage 4 — auto-apply** (only if spike succeeds): ATS adapters one platform at a time,
      always behind batched approval.

## Gaps found in plan review (2026-07-19, not yet scheduled)

- [x] **Markdown → PDF rendering** — DONE 2026-07-19: `resume-tailor render <id>`
      (markdown → styled HTML → Chromium PDF); master.pdf verified visually.
- [x] **Review queue UX** — DONE 2026-07-20: `resume-tailor jobs review [--status ...]`
      renders verdict · score · rubric breakdown · hard-requirement evidence · rationale ·
      apply URL, fits before tailor. Rubric sub-scores now persisted
      (`jobs.score_breakdown`, additive contract amendment + auto-migration).
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
