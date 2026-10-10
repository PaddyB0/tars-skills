---
description: Read-only overnight review of changed TARS code and configuration across Contract, Spec, and Behaviour, with focused validation and no fixes.
argument-hint: "[<base-ref>]"
---

# /night-code-review [<base-ref>]

Review changed TARS code or configuration while Patrick is away. Report only
evidence-backed findings; never alter the review surface.

Read and follow `.claude/skills/code-review/SKILL.md` completely. This command
adds an unattended activation gate and stricter no-write boundaries around that
skill; it does not replace the skill's Contract, Spec, and Behaviour review.

## Non-negotiable boundary

The repository and every external system remain read-only:

- Root CLAUDE.md hard rules 1 and 3 apply in full (protected paths and the plugin data file; Git is never a transport and never mutated).
- Do not edit, create, move, rename, delete, format, generate, or auto-fix
  repository files. Automatically cleaned test fixtures under the OS temporary
  directory are the only permitted filesystem writes.
- Do not open a PR or post GitHub comments.
- Do not install packages or update lockfiles.
- Do not run a test, linter, formatter, build, or typechecker unless it is
  demonstrably non-mutating. Disable bytecode/cache output or route it to the OS
  temporary directory. If that cannot be done confidently, skip it and report
  the validation gap.
- Do not call external write-capable connectors or deployment tools.
- If a suspected credential appears in a reviewed diff, report only its category
  and tight location. Never reproduce the value in the review.
- Do not review or expose client work merely because it is dirty. Client content
  is outside this command's surface unless it is the binding specification for
  an explicitly included code change.
- If the repository changes while the review is running, re-read affected
  reviewed files once. If they change again, mark the surface unstable and stop
  short of conclusions about those files.

## 1. Pin the review surface

Read `AGENTS.md`, root `CLAUDE.md`, and each scoped `CLAUDE.md` governing a changed
path. Record the branch, HEAD, and complete `git status --short` without changing
anything.

Resolve a literal base commit:

1. If `<base-ref>` was supplied, verify it as a commit and use the merge base
   between it and `HEAD`.
2. Otherwise, on a feature branch with a local `origin/main` ref, use the merge
   base between `HEAD` and that **existing local ref**. Do not fetch. State that
   remote freshness is unverified.
3. Otherwise, on `main`, run
   `git rev-list -1 --before="<TODAY> 00:00" HEAD` using the real date in
   `America/Edmonton`; use the returned literal SHA as the start-of-day base.
4. If no safe base resolves, review only staged, unstaged, and relevant untracked
   files, and state that committed-change coverage is unavailable.

Enumerate all commits and files between the resolved base and `HEAD`, then add
staged, unstaged, and relevant untracked files. Keep the committed and worktree
surfaces distinct in the report.

## 2. Apply the code/config activation gate

Review paths that implement or govern behaviour, including:

- `AGENTS.md`, `CLAUDE.md`, scoped operating manuals, `.codex/`, and `.githooks/`;
- canonical `.claude/commands/` and `.claude/skills/`;
- generated `.agents/skills/` when changed, specifically to detect direct edits
  or mirror drift;
- `scripts/`, `Cowork/os/automations/`, and `Cowork/os/scripts/`;
- `Administrator/FileClasses/` and `Bases/` when changed, even though they are
  protected from unasked edits;
- source, test, manifest, schema, and configuration files elsewhere, except under
  excluded client/data paths.

Exclude ordinary content changes under `CRM/`, `Projects/`, `Milestones/`,
`Tasks/`, `Meetings/`, `Work Sessions/`, `Handoffs/`, `Notes/`,
`Cowork/clients/`, `Cowork/os/knowledge/`, timesheet `outbox/` and `receipts/`,
and generated/binary artifacts. A plan in `Notes/` may be read as the spec but is
not itself a code-review target.

If no code/config path changed, return:

> No TARS code or configuration changed in the pinned surface; review skipped.

Include the base, HEAD, and dirty code/config count, then stop. Do not spend the
night reviewing vault-content churn.

## 3. Recover intent

For every included change:

1. Read its originating user request, TARS task, implementation plan, issue, PR
   text, handoff, or nearby acceptance criteria when available.
2. Separate binding requirements from explanatory notes.
3. If no durable specification exists, use the commit message and changed
   contract as the narrow Spec axis and label that limitation.
4. Never treat implementation code or its tests as independent proof of the
   intended behaviour.

Do not access GitHub during this unattended command. If the binding specification
exists only in a GitHub issue or PR, mark the Spec axis partially unverified and
recommend an interactive review using the contract-required `npx -y gh-axi`.
Never fall back to raw `gh`.

## 4. Review all three axes

Apply `.claude/skills/code-review/SKILL.md`:

- **Contract:** authorization, schema, protected paths, canonical/mirror
  ownership, identity boundaries, Git policy, secrets, and scoped manuals.
- **Spec:** missing requirements, incorrect interpretation, scope creep, and
  acceptance criteria that the diff cannot demonstrate.
- **Behaviour:** execution paths, partial failures, dates, identities,
  idempotency, ordering, concurrency, persistence, error handling, and test
  quality.

Consider every included changed path on all three axes. Do not inflate style
preferences or tool-enforced formatting into findings.

## 5. Validate without mutation

Choose focused checks from the changed paths rather than running every repository
test. Prefer existing sibling tests and documented commands.

For Python checks, set:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
```

Run tests that use the OS temporary directory for fixtures. Do not run a command
that writes snapshots, coverage output, caches, compiled assets, vault notes,
receipts, deployment state, or external records. Static inspection is acceptable
when a safe executable check is unavailable.

Record every command, exit code, skipped validation, and reason. Test failure is
evidence to analyze, never permission to fix.

## 6. Return findings in chat

Do not write a review note or inline comments to an external system.

```markdown
# TARS Overnight Code Review — YYYY-MM-DD

**Surface:** <base SHA>..<HEAD SHA> plus <staged/unstaged/untracked summary>
**Assumption:** <why this base is safe>
**Spec:** <source, or "no durable spec found">

## Findings

### [P1] <short actionable title>
- Axis: Contract | Spec | Behaviour
- Location: `path:line`
- Scenario: <how it fails>
- Impact: <why it matters>
- Direction: <smallest credible correction direction; do not implement>

## Validation
- PASS/FAIL/SKIPPED — `<command>` — <result or reason>

## Residual uncertainty
- <what could not be proven>

## Surface inventory
- <every reviewed path, grouped by committed/worktree>
```

Order findings `P0` through `P3`. If there are no findings, say so plainly before
validation and residual uncertainty. A clean review means no defect was found in
the pinned surface; it does not certify untested external state.
