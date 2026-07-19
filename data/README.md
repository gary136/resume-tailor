# data/ — per-user runtime data

Everything here except this README is git-ignored (resume facts are PII).
Layout (contract: `docs/reference/data-contracts.md`):

- `facts.yaml` — fact inventory, the truth record every resume claim must trace to
- `resumes/*.md` — master resume + variants (markdown, YAML frontmatter, per-bullet fact refs)
- `preferences.yaml` — preference record (voice + accept/reject signals)
- `resume_tailor.db` — SQLite: job records + application log

Create with `resume-tailor init`. Override location via `RESUME_TAILOR_DATA`.
