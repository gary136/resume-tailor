<!-- vendored from ~/.claude/shared/workflow/validate.md @ 2026-07-18
     customized: BACKEND_START=python -m resume_tailor; BUILD_CMD=python -m compileall -q src; SMOKE_TEST=python -m resume_tailor --help
     local edits: deleted n/a lines: RESPONSE_SHAPE, FRONTEND_START -->
Run a complete validation of the current implementation against its success criteria.

---

## 1. Build Verification

```bash
python -m compileall -q src
python -m resume_tailor
python -m resume_tailor --help
```

Build must complete with **zero errors** (lint warnings are errors in CI).
Backend must start without exceptions and return valid responses.

## 2. Type / Static Check

Build output confirms no type errors. Flag any loosely-typed escapes (`any`, etc.) added without justification.

## 3. Success Criteria Verification

For each criterion defined before implementation, verify:

```
## Verification Results

### Functional Requirements
- ✅/❌ [Criterion]: [how verified] — [result]

### Technical Requirements
- ✅/❌ Build: pass / fail
- ✅/❌ Backend startup: pass / fail
- ✅/❌ Types: clean / errors

### Acceptance Conditions
- ✅/❌ [Condition]: [evidence]

**Overall**: ✅ Ready to proceed / ❌ Issues found
```

## 4. Code Quality Check

Review the changed files for:
- [ ] Data fetching in the right layer, not in views (per CLI command → core service (tailor / evaluate / apply) → store (SQLite + resume files))
- [ ] No unstable references in effect/subscription deps
- [ ] Every handler has error handling; failures logged, not swallowed
- [ ] No secrets or hardcoded credentials
- [ ] No stray debug logging in production paths

## 5. Smoke Tests

Requires the app running locally.

```bash
python -m resume_tailor --help
```

Report each result as: `✅ expected output` or `❌ unexpected — [actual output]`.

## 6. Manual Testing Steps

Provide step-by-step instructions for the user to manually verify the feature:
1. Start backend: `python -m resume_tailor`
2. Action steps with expected outcomes
4. Edge cases to check

## Output Summary

- What passed ✅
- What failed ❌ (with specific details)
- What needs manual verification by user
- Whether the implementation is ready to proceed/ship
