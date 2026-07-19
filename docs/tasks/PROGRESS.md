# resume-tailor — progress tracker

Single source of truth for project state. Any session (human or agent) resuming work starts here.
Update this file the moment an item finishes (write-as-you-go rule).

Design reference: `docs/reference/resume-tailor-analysis.html` (mirror of
https://claude.ai/code/artifact/c6a36252-1504-4337-a407-9649ce021d2d — keep both in sync when either changes).

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

## Next (delivery order — each stage usable on its own)

- [ ] **Stage 1a — foundations**: freeze canonical resume schema + data contracts (resume
      record, fact inventory, job record, application log); scaffold package
      (`src/resume_tailor/` core library + Typer CLI shell, pytest, SQLite store).
- [ ] **Stage 1b — phase-1 intake**: interactive intake interview → fact inventory → author
      master resume + start preference record. (No import — authoring only in POC.)
- [ ] **Stage 1c — interactive tailoring loop**: propose direction → confirm → section-by-section
      diffs → accept/reject → save variant, keyed by job family.
- [ ] **Track C spike (parallel, ~2 days)**: can Playwright fill a Greenhouse/Lever form with a
      dummy resume? Outcome decides whether stage 4 gets built.
- [ ] **Stage 2 — job side**: US sourcing connectors (Greenhouse/Lever/Ashby boards, aggregator
      API) behind one interface; fit evaluator (hard requirements gate + soft score, three-way
      branch: fits / tailor / fundamentally-unqualified-skip); manual queue + application log.
- [ ] **Stage 3 — auto-tailoring**: generate variants for "no fit" jobs, validated against the
      fact inventory (no fabrication); reuse variants by job family.
- [ ] **Stage 4 — auto-apply** (only if spike succeeds): ATS adapters one platform at a time,
      always behind batched approval.

## Parking lot (product stage, not POC)

- Web/mobile UI wrapping the same core library; multi-user accounts.
- PDF/Word/markdown importers → canonical schema.
- Taiwan market connectors (104, CakeResume).
- Graduated unattended submission (per ATS + job family, per-user opt-in).
- Credential handling, ToS exposure at scale, resume-data privacy (PII).
