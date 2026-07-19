<!-- vendored from ~/.claude/shared/workflow/write-plan.md @ 2026-07-18
     customized: BACKEND_START=python -m resume_tailor; BUILD_CMD=python -m compileall -q src; TASKS_DIR=docs/tasks/
     local edits: none -->
Create a task document at docs/tasks/<FEATURE-NAME>.md that carries a plan through three agents:
planner → reviewer → implementer.

This skill is for the **planning agent**. Use it after `/plan` has produced a complete analysis.
The task document replaces informal chat summaries — it is the single artifact passed between agents.

---

## Step 1 — Create the document
Save to docs/tasks/<FEATURE-NAME>.md (kebab-case filename). Fill in every section from the plan you
just produced. Sections marked *(planning agent)* are yours now; leave *(review agent)* and
*(implementation agent)* sections blank.

## Document template

```markdown
# Task: <Feature Name>

**Status**: Draft
**Created**: <date>
**Branch**: <branch name, if known>

---

## 1. Requirements
### Goal
<One sentence — what this feature/fix achieves.>
### Success criteria
- <Measurable outcome 1>
- <Measurable outcome 2>
### Out of scope
- <Anything explicitly not included>

---

## 2. Current Behavior
<Concrete — user action → system response → outcome.>
### Current flow
\`\`\`
<ASCII or Mermaid diagram of the current flow>
\`\`\`

---

## 3. Proposed Solution
<What changes and why.>
### Proposed flow
\`\`\`
<ASCII or Mermaid diagram of the proposed flow>
\`\`\`
### Key decisions
- <Decision and reasoning>

---

## 4. Implementation Phases
Each phase must pass Gate 1 (independently testable), Gate 2 (one-sentence goal without "and"),
and Gate 3 (150–350 lines of production code changed).

### Phase 1 — <Title>
**Goal**: <One sentence, no "and">
**Files to change**:
- `path/to/file` — <what changes>
**Estimated lines changed**: ~<N> (excluding tests)
**Test criteria**: <What a passing test proves>

<!-- repeat for each phase -->

---

## 5. Review Notes
*(review agent fills this section — do not edit manually)*

**Decision**: [ ] Approved  [ ] Approved with changes  [ ] Needs rework
### Simulation findings
<!-- Flaw / What would happen / Fix applied — or "Simulation complete — no flaws found." -->
**Reviewed by**: <review agent>
**Date**: <date>

---

## 6. Implementation Log
*(implementation agent fills — one entry per phase, after commit)*

### Phase 1 — <Title>
**Status**: [ ] Pending  [ ] In Progress  [ ] Complete
**Commit**: `<sha>`
**Files changed**:
- `path/to/file`
**Tests**: X passed / Y failed — Build: pass / fail
**Manual test steps**:
1. [User action] → [function/route] → [actual result] ✅/❌
**Success criteria**:
- [ ] <criterion from § 1> ✅/❌
**Notes**: <anything unexpected, blockers, deviations>

<!-- repeat for each phase -->

---

## 7. Final Verification
*(implementation agent fills after all phases)*
- [ ] All phases complete
- [ ] python -m compileall -q src passes with zero errors
- [ ] python -m resume_tailor starts without errors
- [ ] No type errors in build output

**Success criteria from § 1** — verify each end-to-end:
- [ ] <copy each criterion from § 1 here> ✅/❌
```

---

## Step 2 — Passing to the next agent
| Next step | Skill to invoke | When |
|-----------|----------------|------|
| Review the plan (separate agent) | `review-plan <feature>` | Always — before implementing |
| Implement autonomously | `implement` | After plan Approved, no per-phase approval |
| Implement with manual approval | `implement-review` | After plan Approved, user approves each phase |
| Full pipeline (review + implement) | `ship` | Run all stages automatically |

## Step 3 — Updating status
`Draft` (planner) → `Under Review` / `Approved` / `Needs Rework` (reviewer) →
`In Progress` / `Complete` (implementer). Update the header **Status** as it moves.
