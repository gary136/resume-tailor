<!-- vendored from ~/.claude/shared/workflow/ship.md @ 2026-07-18
     customized: STANDARDS_DIR=docs/standard/; TASKS_DIR=docs/tasks/
     local edits: none -->
Orchestrate the full plan → review → implement pipeline in a single command.

Run all stages in sequence. Do not skip stages or proceed past a failed review.

---

## Stage 1 — Write the plan to a file
Follow `write-plan` exactly.
- Derive the feature name from the plan already produced in this conversation (kebab-case).
- If no plan exists yet, run `plan` first and wait for the analysis before continuing.
- Save to docs/tasks/<feature-name>.md, fill §§ 1–4, leave §§ 5–7 blank, Status `Draft`.
- Tell the user the file path before moving on.

## Stage 2 — Review (separate agent)
Spawn a **new Agent** (not a continuation of this conversation) — the reviewer must NOT have access
to the planning conversation. Pass this opening prompt:

```
Please review the plan in docs/tasks/<FEATURE-NAME>.md.
Set Status to "Under Review" immediately, then proceed.

Simulate the implementation mentally and find flaws before any code is written.

Step 1 — Read the real codebase, not just the plan. Read every file in § 4 and any file that
  calls or is called by them. Verify against real code.
Step 2 — Simulate each phase: which functions run, what data flows, what the user sees; would the
  app work if only this phase existed; edge cases (empty data, network error, race condition,
  missing env var, null field) the plan doesn't handle; unmentioned interactions with existing code.
Step 3 — Trace the end-to-end flow (§ 3): does each step follow; are all § 1 criteria satisfied?
Step 4 — Check phase gates: testability, one-sentence goal without "and", 150–350 lines, ordering.

If you find a flaw: state what and where; describe what would actually happen; propose a fix;
  update §§ 3–4 directly; record in § 5; set Status "Approved with changes" or "Needs Rework".
If no flaws: don't modify §§ 1–4; fill § 5 "Simulation complete — no flaws found."; Status "Approved".
Only modify the plan if there is a real flaw.

§ 5 format:
**Decision**: Approved / Approved with changes / Needs Rework
### Simulation findings
> **Flaw**: <what and where>
> **What would happen**: <concrete failure>
> **Fix applied**: <what changed in §§ 3–4>
(or "Simulation complete — no flaws found.")
**Reviewed by**: review agent  **Date**: <date>

Reference files: CLAUDE.md, docs/standard/ANALYSIS_AND_PLANNING.md
```

After the review agent finishes, read § 5 of the task doc.

## Stage 3 — Gate check
| Status | Action |
|--------|--------|
| `Approved` | Proceed to Stage 4 |
| `Approved with changes` | Show the user the changes made, ask for confirmation, then proceed |
| `Needs Rework` | Show the flaws found. **STOP. Do not implement.** Ask the user to revise the plan. |

## Stage 4 — Implement autonomously
Follow `implement` exactly.
- The plan is already approved — do not re-check.
- Per phase: implement → build/test → simulate review → commit → log. Proceed to the next phase
  without stopping for user approval.
- Fill § 6 after each phase commit; fill § 7 after all phases; set **Status** to `Complete`.
