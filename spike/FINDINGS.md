# Track C spike findings — 2026-07-19

**Question:** can Playwright fill a Greenhouse application form with a dummy resume?
**Answer: YES — GO for stage 4 (auto-apply).**

## Evidence

`spike/greenhouse_spike.py` against two live postings (GitLab, Reddit — both on the current
job-boards.greenhouse.io React UI): 5/5 fields each — first/last name, email, phone by stable
`#id` selectors, resume PDF via `input[type=file]`. Screenshots: `spike/out/attempt-{1,2}.png`
(gitignored with `spike/dummy_resume.pdf`). Nothing was submitted; the script has no submit
code path by design.

Bonus for stage 2: the public board API needs no auth —
`https://boards-api.greenhouse.io/v1/boards/<board>/jobs` (167–411 jobs for gitlab /
anthropic / reddit); `?content=true` adds the JD.

## What stage 4 still has to solve (adapter work, not feasibility blockers)

1. **Custom questions per company** — React dropdowns (work authorization, visa, source),
   LinkedIn URL, cover letter. Varies per posting; the adapter needs an answer-mapping layer
   fed by the preference record + fact inventory.
2. **reCAPTCHA** — a badge is present on the form. Fill is unaffected, but submit may be
   challenged. Unknown until a real (user-approved) submission; plan for headed-browser
   submission with the user present in early batches.
3. **Self-identification sections** (gender / veteran / disability) — voluntary; policy
   decision for Gary at stage 4, not automated by default.
4. **Old embed UI** (`boards.greenhouse.io/<company>`) not yet tested — selectors kept as
   fallbacks in the spike script.
