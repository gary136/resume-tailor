<!-- vendored from ~/.claude/shared/workflow/handoff.md @ 2026-07-18
     customized: DEPLOY_TARGET=local (POC); HANDOFF_DIR=docs/handoffs/
     local edits: none -->
Produce a structured handoff summary for this conversation so a new agent can resume without
re-reading the full history.

Write the full summary in the chat AND save it to docs/handoffs/HANDOFF-<task-slug>.md where
`<task-slug>` is the kebab-case name of the current task.

Both are mandatory. Skipping the file save defeats the purpose of the handoff.

---

## Summary format
Use this exact structure. Omit any section that has nothing to record.

### Active Task
One sentence: what the user is trying to achieve right now. Include success criteria if stated.

### Completed This Session
Bullet list — what was finished, including file paths changed. Be specific: "Updated `path` line N
to do X", not "fixed the thing".

### In Progress
What was started but not finished. Include the exact stopping point: last file edited, last command
run, last test result seen.

### Next Steps
Ordered list, specific enough that a new agent can act without asking.

### Files Changed This Session
Every file created/edited/deleted. Format: `path/to/file` — one-line description of change.

### Key Decisions & Context
Decisions not obvious from reading the files — reasoning, tradeoffs, constraints discovered.

### Known Issues / Blockers
Anything broken, incomplete, or requiring the user's input before proceeding.

### Test State
Last known results — build: pass/fail; backend startup: pass/fail; deploy (local (POC)):
pass/fail/not yet.

### How to Resume
Two or three sentences a new agent can use as its opening prompt.

---

## Rules for writing the summary
- **Concrete over vague.** File paths, line numbers, commit SHAs, exact error messages.
- **State, not narration.** Where things stand, not the story of how we got there.
- **Enough to act.** A new agent reading only this should continue without clarifying questions.
- **No padding.** Skip sections with nothing to record.
