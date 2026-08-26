---
name: tdd
description: Implement authorized software behaviour test-first through vertical red-green-refactor slices at stable public seams. Use when the user requests TDD or test-first delivery, or when an authorized feature or bug fix needs durable regression protection.
---

# Test-Driven Development

Build one observable behaviour at a time. Keep every slice green before opening the
next one.

## 1. Establish authority and target behaviour

1. Confirm that the request authorizes implementation, not diagnosis only.
2. Read the repository contract, scoped instructions, originating spec or task, and
   relevant existing tests.
3. Preserve unrelated changes in a dirty worktree.
4. State the next behaviour as a concrete input, action, and observable result.

If a material product or architecture decision is unresolved, ask before encoding it
in a test. Otherwise choose the narrowest reasonable interpretation and state it.

## 2. Choose the seam

Test through the highest stable public interface that can reproduce the behaviour:
command, HTTP boundary, UI interaction, exported function, or other caller-visible
surface. Prefer an existing seam. Introduce a new seam only when the behaviour cannot
be observed cleanly through the current design.

Avoid tests that:

- assert private implementation details;
- mock internal collaborators merely to reach a line;
- recompute the expected result with the same logic as production;
- use snapshots without a reviewed, independent expected value.

## 3. Run one red-green-refactor slice

### Red

Write one focused test for the next behaviour. Run it and confirm it fails for the
intended reason. A test that errors during setup or fails on an unrelated condition
is not red.

### Green

Make the smallest coherent production change that satisfies the test. Do not
anticipate later slices or add unrequested flexibility. Run the focused test until
it passes.

### Refactor

Improve names, duplication, and structure only while the slice remains green. Keep
the public behaviour fixed. Rerun the focused test after each meaningful refactor.

Repeat with the next vertical slice. Do not write a horizontal batch of imagined
tests before any implementation feedback arrives.

## 4. Validate in widening circles

After each slice, run the smallest relevant test target. At stable checkpoints, run
the affected package's typecheck, lint, or equivalent static checks. At completion:

1. run every focused test added or changed;
2. run the relevant broader suite;
3. run the repository's required validation gates;
4. run TARS `/lint` after any batch of vault-note writes;
5. inspect the final diff for scope creep and accidental user-change overlap.

For client delivery work, consult `Cowork/os/knowledge/index.md` before building.
Never edit TARS protected paths unasked, run raw `git push`, or bypass
`scripts/tars_push.py`.

## 5. Hand off

Summarize the behaviours delivered, seams tested, commands run, and any validation
not run. For a substantial or high-risk diff, apply the `code-review` skill before
declaring the implementation complete.

Do not commit, push, open a PR, or update PM state unless the user requested that
workflow.

## Completion criterion

Complete only when each new behaviour was observed red before green, all relevant
tests and required checks pass, the final diff remains within the authorized scope,
and no unexplained failure or temporary test artifact remains.
