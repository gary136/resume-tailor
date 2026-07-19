<!-- vendored from ~/.claude/shared/workflow/analyze.md @ 2026-07-18
     customized: STANDARDS_DIR=docs/standard/
     local edits: none -->
Perform a deep analysis of the code, system, or problem described above.

This is a read-only investigation — no code changes. Produce findings and recommendations only.

---

## 1. Scope the Analysis
State clearly:
- What is being analyzed (component, feature, bug, performance issue, architecture question)
- What question needs to be answered

## 2. Read the Relevant Code
Identify and read:
- The primary file(s) directly involved
- Their dependencies (across the layer chain: CLI command → core service (tailor / evaluate / apply) → store (SQLite + resume files))
- Any related docs in docs/standard/ or the project's docs

## 3. Document Current Behavior
Trace what actually happens step by step through the stack (Python 3.12 CLI (Typer) + core library; anthropic SDK; Playwright (apply engine); SQLite + markdown resume files):
- Follow the layer chain: CLI command → core service (tailor / evaluate / apply) → store (SQLite + resume files)
- Note the actual data shapes at each step

## 4. Identify Issues or Gaps
For each finding:
```
**Finding**: [what was found]
**Location**: [file:line]
**Impact**: [what this affects]
**Severity**: High / Medium / Low
```

## 5. Recommendations
For each issue found:
```
**Recommendation**: [what to do]
**Rationale**: [why this approach]
**Effort**: Small / Medium / Large
```

## 6. Summary
- Total issues found
- Critical issues (must fix before shipping)
- Improvement opportunities (nice to have)
- Suggested next step (use `/plan` to design a solution, or specific quick fixes)

**Do not make any code changes during analysis.** Present findings only.
