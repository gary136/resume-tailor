<!-- vendored from ~/.claude/shared/workflow/implement-review.md @ 2026-07-18
     customized: BUILD_CMD=python -m compileall -q src; TASKS_DIR=docs/tasks/; TEST_CMD=pytest <file>
     local edits: none -->
Implement the plan in docs/tasks/<FEATURE-NAME>.md **one phase at a time**, stopping for
explicit user approval after each phase before proceeding.

The plan must be Approved in § 5 before starting.

---

## Cycle per Phase: Implement → Test → Present → Wait for Approval → Commit → Log

### 1. Implement
- Define success criteria BEFORE coding
- Make minimal changes for this phase only, following CLI command → core service (tailor / evaluate / apply) → store (SQLite + resume files)
- Create tests for new code

### 2. Test & Verify
```bash
pytest <file>
python -m compileall -q src
```
Verify all success criteria are met. Fix failures before presenting.

### 3. Present Results
- What changed and why
- Test results (pass/fail counts), build status
- Success criteria verification (✅/❌ each)
- Manual testing steps the user can follow

**Manual verification checklist** — explicitly list anything automated tests/code tracing cannot
confirm. Format as a numbered browser checklist. If nothing, write "No manual verification needed."

### 4. Wait for Approval
**STOP HERE. Do not proceed to the next phase.**

Wait for explicit approval ("proceed", "approved", "looks good", or similar).
- Do NOT assume silence = approval
- If feedback is given, make changes, re-test, present again

### 5. After Approval — Commit
```
[type](scope): brief description

- Change 1
- Files: file1, file2
```

### 6. Log — update § 6 of the task doc
Record commit SHA, files changed, test/build results, success criteria (✅/❌), notes.
Set the phase **Status** to `[x] Complete`, then proceed to the next phase (repeat from step 1).

---

## After All Phases
Fill § 7 Final Verification, set task doc **Status** to `Complete`, and give a brief completion
summary (what was built, phases completed, files changed, production readiness).
