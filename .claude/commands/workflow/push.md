<!-- vendored from ~/.claude/shared/workflow/push.md @ 2026-07-18
     customized: structural only
     local edits: none -->
Commit all uncommitted changes and push to origin.

---

## Phase 1 — Commit all uncommitted changes
1. Run `git status` to see what is untracked or modified.
2. Stage and commit in logical groups — one commit per concern. Do not batch unrelated changes.
3. Follow conventional commit style: `type(scope): description`
   (`feat(backend):`, `fix(deploy):`, `chore(workflow):`, `docs(tasks):`, etc.)
4. Never commit: `.env` files, secrets, caches, or build artifacts.
5. After all commits, run `git status` to confirm the working tree is clean.

## Phase 2 — Push
Run `git push` to the current branch's upstream.
Confirm the push succeeds and report the final commit hash and how many commits were pushed.
