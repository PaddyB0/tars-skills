---
name: safe-push
description: Validate and publish committed TARS changes through the repository's fail-closed exact-SHA push gate. Use when the user invokes /safe-push or $safe-push, asks to push, publish, ship, or safely validate TARS changes before a push, or asks to run the guarded push preflight. Never use raw git push.
---

# Safe Push

Publish only through `scripts/tars_push.py`. Treat that script as the enforcement
layer; never reproduce, weaken, or bypass its checks.

## 1. Establish scope and authority

1. Read root `AGENTS.md`, `CLAUDE.md`, and any scoped contract.
2. Inspect the current branch, `HEAD`, and `git status --short`.
3. Preserve unrelated work. The intended changes must already be committed and the
   worktree must be clean. Do not stage, commit, stash, reset, rebase, or repair
   blockers unless the user separately authorizes that work.
4. Distinguish validation from publication:
   - For a check, validation, or preflight request, stop after a successful preflight.
   - For an explicit push, publish, or ship request—or a bare explicit invocation of
     this skill—continue to the guarded push after preflight.

## 2. Confirm repository protection

Run:

```bash
git config --local core.hooksPath
```

It must return `.githooks`. If this clone has not been initialized, configure it once:

```bash
git config --local core.hooksPath .githooks
```

Do not continue if the hook path cannot be made active.

## 3. Run the immutable preflight

Run:

```bash
python scripts/tars_push.py
```

Read and report every blocker. Do not bypass or silently fix a failure. A valid
preflight must print `PREFLIGHT PASSED` for the reviewed full commit SHA. Record that
SHA; all later confirmation applies only to that object.

If the branch or `HEAD` changes, or the worktree becomes dirty, discard the prior
preflight result and start again.

## 4. Publish only when authorized

For an existing remote branch, run:

```bash
python scripts/tars_push.py --push
```

For a new feature branch, add `--allow-new-branch` only after verifying the exact
branch name:

```bash
python scripts/tars_push.py --push --allow-new-branch
```

Let the user complete the interactive exact-SHA confirmation. In a non-interactive
session, pass `--confirm <reviewed-sha>` only when the current request explicitly
authorizes publication. Never infer push authority from a review-only request.

Never run raw `git push`, force-push, or bypass a gate failure. Direct `main` pushes
are limited to vault content; OS, code, and configuration changes require a feature
branch and PR.

## 5. Report the outcome

Report success only when the gate prints:

```text
PUSH VERIFIED: <remote>/<branch> = <full-sha>
```

Otherwise state that nothing was pushed, include the exact blocker, and identify the
smallest user-authorized next action. Do not open a PR or merge unless the user also
requested that workflow.

## Completion criterion

Complete only when the requested preflight has passed against the current immutable
commit and, when publication was authorized, the remote branch has been verified at
that exact SHA.
