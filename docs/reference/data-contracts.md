# Data contracts (stage 1a) — FROZEN 2026-07-19

Status: **frozen 2026-07-19** after user review (all four open items approved: YAML fact
inventory, per-bullet fact-ref comments, hard UNIQUE double-apply constraint, Python 3.13).
Implemented in `src/resume_tailor/contracts.py` (pydantic models) and
`src/resume_tailor/store/schema.sql` (SQLite DDL). The three dev tracks build against these;
changes after freeze require a dated note here.

Provenance note: the `UNIQUE(job_id)` constraint was not in the original design doc verbatim —
the doc assigns the application log the job of "preventing double-applying"; the constraint is
the chosen mechanism for that, approved at freeze.

**Amendment 2026-07-20 (additive):** `jobs.score_breakdown` (JSON of the rubric
components behind `soft_score`) — needed so the review queue can show *why* a score
landed. Additive only; `init_db` migrates existing stores with ALTER TABLE, and
readers tolerate its absence.

**Amendment 2026-07-19 (user decision, post-freeze):** `Fact` gains an optional
`fidelity: verified | plausible` field (default `verified`). Purpose of the tool is getting
interviews, not documentary accuracy: *exaggerated* claims are acceptable, *impossible* ones
are not. Background-checkable facts (employers, titles, dates, degrees, certifications) must
stay `verified`; achievement metrics/framing may be `plausible` — exaggerated-but-possible,
internally consistent. The traceability rule is unchanged and is what enforces the
"not impossible" bound: every resume claim must still reference a fact rooted in a real
role/activity.

The tailoring engine's job is *calibrated* exaggeration (user, 2026-07-19): claims should sit
in the maximum-credible zone — impressive, but never enough to arouse doubt. Heuristics:
metrics must match org scale and role seniority (interns don't save hundreds of millions);
estimate-shaped numbers ("40%", "1M+") over suspicious precision; every claim needs a
30-second improvisable interview backstory; checkable facts never exaggerate.

Storage split (per stack decision "SQLite + markdown resume files"):

| Artifact | Where | Why |
|---|---|---|
| Fact inventory | `data/facts.yaml` | The truth record. Must be human-auditable and hand-correctable — YAML, git-diffable. |
| Master resume + variants | `data/resumes/*.md` | Markdown with YAML frontmatter; human-readable, diffs cleanly in the accept/reject loop. |
| Preference record | `data/preferences.yaml` | Accumulated voice + edit signals; small, human-readable. |
| Job records | SQLite `jobs` table | Fetched in bulk, queried/filtered — transactional store. |
| Application log | SQLite `applications` table | Append-mostly log; uniqueness constraint prevents double-applying. |

`data/` is per-user runtime data, git-ignored except a committed `data/README.md`.

---

## 1. Fact inventory — `data/facts.yaml`

Source of truth for every claim in every resume. Built at intake **before** the master is
written; nothing enters a resume that doesn't trace to a fact here.

```yaml
version: 1                # bumped on any edit
updated_at: "2026-07-19"
facts:
  - id: role-acme-2021          # stable slug, never reused after deletion
    kind: role                  # role | education | skill | achievement |
                                # certification | project | language | other
    statement: "Senior Backend Engineer at Acme Corp"   # one-line canonical truth
    org: "Acme Corp"            # optional
    date_start: "2021-03"       # optional, YYYY-MM
    date_end: null              # null = present
    details: "Payments team, 6 engineers"               # optional free text
    parent_id: null             # achievements/projects point at their role
    tags: [backend, python]
    source: "intake 2026-07-19" # provenance — which interview/session added it
```

Rules:
- `id` is permanent. Corrections edit the fact in place (version bump); deletions leave the id
  retired (validator treats references to retired ids as errors).
- `kind: achievement` SHOULD have a `parent_id` pointing at a `role` or `project`.
- No derived/inflated statements: the statement is what the user actually said, tightened for
  grammar only.

## 2. Resume record — `data/resumes/<resume_id>.md`

Markdown body + YAML frontmatter. One file per master/variant.

```markdown
---
resume_id: master            # or e.g. backend-platform-v1
kind: master                 # master | variant
job_family: null             # required for variants, e.g. "backend-platform"
based_on: null               # variants: resume_id + version of the master they derive from
version: 3                   # bumped every accepted edit
status: draft                # draft | confirmed (user accepted)
created_at: "2026-07-19"
updated_at: "2026-07-19"
---
# Gary <Lastname>
...

## Experience
### Senior Backend Engineer — Acme Corp (2021–present)
- Cut p99 checkout latency 40% by re-architecting the payment queue. <!-- facts: ach-acme-latency -->
- Led migration of a 6-engineer team to an event-driven architecture. <!-- facts: ach-acme-migration, role-acme-2021 -->
```

**Claim traceability (the no-fabrication mechanism):** every bullet line ends with an HTML
comment `<!-- facts: id[, id…] -->`. The validator
(`resume_tailor.validation.validate_resume`) fails a resume if any bullet lacks fact refs or
references an unknown/retired fact id. Headings and prose section intros don't need refs;
bullets (lines starting `- `) do.

- Variants are keyed by **job family**, not per-JD (prevents sprawl). `job_family` is a free
  slug assigned when the first variant for that family is created; the job record carries the
  same slug.

## 3. Job record — SQLite `jobs`

```sql
CREATE TABLE jobs (
  job_id            TEXT PRIMARY KEY,        -- uuid4
  source            TEXT NOT NULL,           -- greenhouse | lever | ashby | aggregator | manual
  external_id       TEXT,                    -- id at the source, if any
  url               TEXT NOT NULL,
  company           TEXT NOT NULL,
  title             TEXT NOT NULL,
  location          TEXT,
  remote            INTEGER,                 -- 0/1/NULL(unknown)
  description_text  TEXT NOT NULL,           -- plain text, post-scrape
  job_family        TEXT,                    -- assigned during triage; matches variant slug
  fetched_at        TEXT NOT NULL,           -- ISO 8601
  -- fit evaluation (three-way branch)
  fit_status        TEXT NOT NULL DEFAULT 'pending',
                    -- pending | fits | tailor | skip
  hard_requirements TEXT,                    -- JSON: [{requirement, met, evidence_fact_id|null}]
  soft_score        INTEGER,                 -- 0–100, only meaningful when hard reqs all met
  score_breakdown   TEXT,                    -- JSON: rubric components (config/rubric.yaml)
  fit_rationale     TEXT,
  evaluated_at      TEXT,
  UNIQUE (source, external_id),
  UNIQUE (url)
);
```

Branch semantics (from the design doc): any hard-requirement miss → `skip`; hard reqs met +
high soft score → `fits` (apply with existing master/variant); hard reqs met + low soft
score → `tailor` (generate/reuse a variant). Thresholds live in config, not the schema —
they'll be tuned against the user's judgment.

## 4. Application log — SQLite `applications`

```sql
CREATE TABLE applications (
  application_id TEXT PRIMARY KEY,           -- uuid4
  job_id         TEXT NOT NULL REFERENCES jobs(job_id),
  resume_id      TEXT NOT NULL,              -- which resume file was used
  resume_version INTEGER NOT NULL,           -- pinned version at submit time
  status         TEXT NOT NULL DEFAULT 'queued',
                 -- queued | approved | submitted | confirmed | failed | withdrawn_by_user
  batch_id       TEXT,                       -- approval batch (batched-approval gate)
  method         TEXT,                       -- manual | playwright-greenhouse | playwright-lever | …
  queued_at      TEXT NOT NULL,
  approved_at    TEXT,                       -- set only by explicit user approval
  submitted_at   TEXT,
  notes          TEXT,
  UNIQUE (job_id)                            -- one application per job, ever → no double-apply
);
```

Invariants:
- `status` may reach `submitted` only from `approved`, and `approved_at` is set only by the
  user's batch-approval action — the library enforces this transition, no code path bypasses it.
- `UNIQUE (job_id)` is the double-apply guard at the storage layer.

## 5. Preference record — `data/preferences.yaml`

Started in stage 1b, accumulated by every interactive session; auto-tailoring (stage 3) reads it.

```yaml
voice:                       # standing style notes, user-confirmed
  - "Short bullets, number-first, no adjectives like 'passionate'"
edit_signals:                # every accept/reject in the interactive loop appends one
  - date: "2026-07-20"
    job_family: backend-platform
    proposal: "Lead with the latency achievement"
    verdict: accepted        # accepted | rejected | edited
    note: ""
```

---

## Open items for user review (freeze checklist)

1. Fact inventory as YAML file (not SQLite) — chosen for hand-auditability. OK?
2. Bullet-level `<!-- facts: … -->` comments as the traceability mechanism. OK?
3. One-application-per-job as a hard DB constraint (re-applying after rejection would need a
   deliberate schema change). OK?
4. Python 3.13 (Homebrew) instead of 3.12 — no 3.12 on this machine; `requires-python >= 3.12`.
