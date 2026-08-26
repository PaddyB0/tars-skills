---
name: code-review
description: Review a TARS code or configuration diff across Contract, Spec, and Behaviour axes without changing it. Use when the user asks to review code, current changes, a branch, a pull request, or work since a commit or other fixed point.
---

# Code Review

Review only. Do not fix findings, alter the diff, stage files, or mutate GitHub unless
the user separately asks.

## 1. Pin the review surface

1. Read `AGENTS.md`, root `CLAUDE.md`, and any scoped contract such as
   `Cowork/CLAUDE.md`.
2. Record `git status --short` and preserve unrelated user work.
3. Resolve the requested fixed point and enumerate the exact commits and files under
   review.
4. For current worktree review, include staged, unstaged, and relevant untracked
   files. For branch review, compare against the merge base with the requested base.
5. For a GitHub PR or issue, use `npx -y gh-axi`; never use raw `gh`.

If the fixed point is omitted, infer the safest conventional base from the current
branch and repository state, state the assumption, and ask only when competing bases
would materially change the review.

## 2. Recover the intended change

Use the user's request as the primary specification. Supplement it with the linked
TARS Task, implementation plan, issue, PR body, acceptance criteria, and relevant
comments. Distinguish binding requirements from explanatory context.

If no durable spec exists, review against the explicit request and report that the
Spec axis is necessarily narrower.

## 3. Review three independent axes

### Contract

Check the diff against repository instructions and invariants, including:

- authorization and requested scope;
- TARS schema values, dates, wikilinks, and mapped-folder rules;
- protected paths and immutable source boundaries;
- client/engagement/work-folder identity separation;
- canonical skill and generated-mirror ownership;
- GitHub and guarded-push policy;
- documented code standards and existing architectural decisions.

Treat contract violations as defects, not style preferences.

### Spec

Check for:

- missing or partial requirements;
- incorrect interpretations;
- unrequested behaviour or scope creep;
- acceptance criteria that cannot be demonstrated;
- implementation decisions that contradict the originating plan.

Quote or identify the requirement behind each Spec finding.

### Behaviour

Trace changed execution paths and look for:

- incorrect results, state transitions, or error handling;
- edge cases at dates, identities, retries, idempotency, and partial failure;
- regressions outside the happy path;
- concurrency, ordering, or persistence hazards;
- tests that miss the real seam, pass tautologically, or fail to protect the change.

Run focused read-only checks and tests when they materially improve confidence. Do
not report tooling-enforced formatting nits unless the tool actually fails.

## 4. Report actionable findings

Prioritize each finding:

- `P0` — destructive, security-critical, or system-wide failure;
- `P1` — likely incorrect behaviour or contract violation requiring correction;
- `P2` — real defect in a narrower or less likely case;
- `P3` — worthwhile improvement with limited impact.

For every finding, provide a short title, tight file/line location, the failing
scenario, why it matters, and the smallest credible correction direction. Do not
inflate preferences into defects.

Keep Contract, Spec, and Behaviour findings distinct so one axis cannot mask another.
After findings, state which validations ran, what could not be validated, and any
residual uncertainty. If there are no findings, say so plainly.

## Completion criterion

Complete only when the exact review surface is explicit, every changed path has been
considered under all three axes, each finding is evidence-backed and actionable, and
validation gaps are visible. Leave the worktree unchanged.
