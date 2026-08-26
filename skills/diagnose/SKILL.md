---
name: diagnose
description: Diagnose hard software defects and performance regressions by establishing a red-capable reproduction loop, minimising the failure, testing ranked hypotheses, and reporting a proven root cause. Use when the user asks to diagnose, debug, investigate, or explain broken, flaky, slow, or regressed behaviour. Diagnosis-only by default; do not implement a fix unless the user explicitly requests one.
---

# Diagnose

Prove the cause before proposing a fix. Treat this workflow as investigation
authority, not implementation authority.

## 1. Establish the contract and symptom

1. Read the repository contract and any scoped instructions before investigating.
2. Preserve unrelated user changes and record the current repository state.
3. Restate the exact observed symptom, expected behaviour, affected surface, and
   known-good state. Separate observations from assumptions.
4. Identify one pass/fail signal that would distinguish this defect from nearby
   failures.

Do not change tracked files during a diagnosis-only request. Prefer existing tests,
read-only commands, runtime inspection, or a harness in the OS temporary directory.
Ask before adding tracked instrumentation.

## 2. Build a tight feedback loop

Find one agent-runnable command that exercises the real failure path and can detect
the user's exact symptom. Prefer, in order:

1. an existing focused test;
2. a CLI, HTTP, or data-fixture invocation;
3. a browser or UI automation check;
4. a replay of captured input;
5. a temporary harness, differential check, or seeded stress loop.

Run the command at least once. Tighten it until it is as deterministic, specific,
and fast as the environment permits. If no credible loop can be built, report what
was attempted and what artifact or access is missing; do not substitute speculation.

## 3. Reproduce and minimise

Confirm the loop produces the reported failure rather than a convenient adjacent
failure. Remove inputs, configuration, callers, and steps one at a time, rerunning
after each cut. Stop when every remaining element is load-bearing.

## 4. Test ranked hypotheses

Generate three to five falsifiable hypotheses. For each, state the observation that
would support it and the observation that would rule it out. Rank them by evidence,
not familiarity.

Share the ranked list as a concise progress update when user domain knowledge could
materially re-rank it, then continue unless that knowledge is essential.

Change one variable per probe. Prefer debugger or REPL inspection, then narrowly
targeted logs. For performance regressions, measure a baseline and use profiling or
bisection rather than broad logging.

## 5. Prove the cause

Demonstrate that the winning hypothesis explains the minimised case and the original
case. Capture the causal chain and the evidence that ruled out the strongest
alternative. Remove temporary artifacts and instrumentation before reporting.

## 6. Report and stop

Report:

- the exact symptom and reproduction command;
- the proven root cause and causal chain;
- the decisive evidence;
- affected scope and remaining uncertainty;
- the smallest credible fix direction;
- the correct regression-test seam, if one exists.

Do not implement, commit, push, or mutate external state unless the user separately
authorized a fix. When a fix is authorized, hand the proven reproduction and seam to
the `tdd` skill.

## Completion criterion

Complete only when the original symptom is reproducible or the missing prerequisite
is explicit, the cause is supported by evidence rather than plausibility, temporary
diagnostic changes are gone, and the report cleanly separates fact from inference.
