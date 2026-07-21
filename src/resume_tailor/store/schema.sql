-- Canonical SQLite schema (stage 1a). Spec: docs/reference/data-contracts.md §3–4.

CREATE TABLE IF NOT EXISTS jobs (
  job_id            TEXT PRIMARY KEY,
  source            TEXT NOT NULL,
  external_id       TEXT,
  url               TEXT NOT NULL,
  company           TEXT NOT NULL,
  title             TEXT NOT NULL,
  location          TEXT,
  remote            INTEGER,
  description_text  TEXT NOT NULL,
  job_family        TEXT,
  fetched_at        TEXT NOT NULL,
  fit_status        TEXT NOT NULL DEFAULT 'pending',
  hard_requirements TEXT,
  soft_score        INTEGER,
  score_breakdown   TEXT,           -- JSON: rubric components (see config/rubric.yaml)
  fit_rationale     TEXT,
  evaluated_at      TEXT,
  UNIQUE (source, external_id),
  UNIQUE (url)
);

CREATE TABLE IF NOT EXISTS applications (
  application_id TEXT PRIMARY KEY,
  job_id         TEXT NOT NULL REFERENCES jobs(job_id),
  resume_id      TEXT NOT NULL,
  resume_version INTEGER NOT NULL,
  status         TEXT NOT NULL DEFAULT 'queued',
  batch_id       TEXT,
  method         TEXT,
  queued_at      TEXT NOT NULL,
  approved_at    TEXT,
  submitted_at   TEXT,
  notes          TEXT,
  UNIQUE (job_id)
);
