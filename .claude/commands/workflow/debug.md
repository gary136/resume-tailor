<!-- vendored from ~/.claude/shared/workflow/debug.md @ 2026-07-18
     customized: BACKEND_START=python -m resume_tailor; BUILD_CMD=python -m compileall -q src; SMOKE_TEST=python -m resume_tailor --help
     local edits: none -->
Follow this debugging workflow for the issue described above.

Do not guess or jump to fixes. Diagnose first.

---

## Step 1 — Reproduce & Define the Problem
- State the exact symptom (error message, wrong behavior, expected vs actual)
- Identify when it occurs (which action, which route, which component)
- Confirm it's reproducible, or note the pattern if intermittent

## Step 2 — Trace the Code Path

Walk the layer chain for this stack (CLI command → core service (tailor / evaluate / apply) → store (SQLite + resume files)). For each layer, ask what it receives and returns.

For **frontend bugs**:
- Which component renders the wrong output?
- Which hook/state provides the data? What does it return?
- Which call fetches it? What does the response look like?
- Any effect/subscription dependency issues causing stale data or loops?

For **backend bugs**:
- Which route/handler is called?
- What does the data query return?
- Is an external call returning empty/erroring?
- Is a background job failing silently? (check server logs)

## Step 3 — Form a Hypothesis
State the suspected root cause as a specific, falsifiable claim:
> "The bug is caused by X in Y file at line ~Z because..."

## Step 4 — Verify the Hypothesis
Read the suspected code. Check:
- Is the hypothesis consistent with the symptom?
- Are there other explanations?
- What evidence confirms or refutes it?

Do NOT apply a fix until the root cause is confirmed.

## Step 5 — Fix
- Make the minimal change that addresses the root cause
- Do not refactor surrounding code unless directly related
- Follow existing patterns (no new abstractions for a bug fix)

## Step 6 — Verify the Fix
```bash
python -m resume_tailor
python -m resume_tailor --help
python -m compileall -q src
```
Confirm the original symptom no longer occurs and no regressions in related functionality.

---

## Common Bug Patterns (project-specific)

TODO(<PROJECT_BUG_PATTERNS>) — fill this table as real bugs appear
<!-- Fill a table of this project's recurring bugs when vendoring, e.g.:
| Symptom | Likely Cause |
|---------|-------------|
| ... | ... |
-->
