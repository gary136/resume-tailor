<!-- vendored from ~/.claude/shared/workflow/implement.md @ 2026-07-18
     customized: BACKEND_START=python -m resume_tailor; BUILD_CMD=python -m compileall -q src; TASKS_DIR=docs/tasks/; TEST_CMD=pytest <file>
     local edits: none -->
Implement the plan in docs/tasks/<FEATURE-NAME>.md **one phase at a time**, with autonomous
self-review. Complete the full cycle — including commit — before moving to the next phase.

The plan must be Approved in § 5 before starting.

---

## Cycle per Phase: Implement → Test → Simulate Review → Commit → Log

### 1. Before Coding — Define Success Criteria
State these BEFORE writing any code:
```
## Phase [N] Success Criteria
### Functional Requirements
- [ ] [what must work]
### Technical Requirements
- [ ] All tests pass
- [ ] python -m compileall -q src succeeds
- [ ] No type errors
### Acceptance Conditions
- [ ] [measurable condition]
```

### 2. Implement & Test
- Make the minimal changes for this phase only
- Follow existing patterns (the layer chain: CLI command → core service (tailor / evaluate / apply) → store (SQLite + resume files))
- Add comments only where logic is non-obvious
- Write tests for new code before marking the phase done: `pytest <file>`
- Build: `python -m compileall -q src` and start check: `python -m resume_tailor`

Verify all success criteria are met. Fix failures before proceeding.

### 3. Simulate User Review
**Act as the user doing a review** — you are no longer the implementer.
- Does it follow project conventions (CLAUDE.md)?
- Are all success criteria from step 1 met?
- Any logic errors, missing error handling, or security issues?

Trace each manual test step through the code:
```
1. [User action] → which function/route handles this
2. [Expected result] → what the code would actually return/render
3. Determine: would the user see the expected result? Yes / No
```
If any step would produce the wrong result, fix and re-simulate before proceeding.

### 4. Present Results
- What changed and why
- Test results (pass/fail counts), build status
- Success criteria verification (✅/❌ each)
- Manual test simulation results

**Manual verification checklist** — list anything automated tests/code tracing cannot confirm
(visual rendering, real auth flows, real-time events, third-party integrations, cross-page state).
Format as a numbered browser checklist. If nothing, write "No manual verification needed."

### 5. Commit
```
[type](scope): brief description

- Change 1
- Files: file1, file2
```

### 6. Log — update § 6 of the task doc for this phase
Fill in: commit SHA, files changed, test pass/fail counts + build status, the manual test steps
traced in step 3 (each ✅/❌), each success criterion (✅/❌), and any notes/deviations.
Then set the phase **Status** to `[x] Complete` and proceed to the next phase (repeat from step 1).

---

## After All Phases — Fill § 7 Final Verification
- Check off each verification item
- Copy each success criterion from § 1 and mark ✅/❌ with evidence
- Set the task doc **Status** to `Complete`

**Do not implement multiple phases in one response.**
