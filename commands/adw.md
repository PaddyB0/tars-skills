---
description: Select a bounded, ADW-style agent workflow preset for TARS work while preserving TARS task contracts, approval boundaries, and evidence gates.
argument-hint: "[preset] <objective> [--commit]"
---

# /adw [preset] <objective> [--commit]

Run a named, serial agent-workflow preset. This is TARS's compact equivalent of
the workflow menu described in the supplied reference: useful stages are made
explicit, but they remain governed by [[AI Agent Workflow Standards]] and the
repository contract.

`<objective>` is required. Omit `<preset>` to use `full` for a non-trivial local
change. Before the first action, state the task contract:
objective, authoritative sources, read/write/external scope, risk class,
acceptance checks, budget, tier/routing reason, and stop conditions. If material
requirements are unresolved, stop for direction rather than choosing a broader
workflow. The tier/routing reason names the model and effort being dispatched.

## Non-negotiable boundaries

- Begin with deterministic inspection and use the least authority and tier that
  can meet the acceptance bar.
- A `scout`, `plan`, or `quality` stage is read-only. It reports evidence; it
  never quietly repairs, rewrites, commits, or publishes.
- A `build` or `document` stage may write only to the named paths in the task
  contract. A separate stage does not expand that authority.
- A repair loop is `observe → one hypothesis → one action → named check`.
  Use the task contract's limit (at most two for normal R1 work); do not repeat
  an unchanged failed action.
- Do not create Tasks, Work Sessions, commits, pushes, PRs, external messages,
  or tenant changes merely because a preset reaches its final stage. Those are
  separate authorities.
- `--commit` is valid only when the user explicitly requested a local commit and
  every mandatory acceptance check has passed. Publication remains a separate
  `/safe-push` workflow governed by the repository's canonical push gate.
- Do not turn this command into a hidden background swarm. Parallel workers need
  independently scoped contracts and a coordinator under the standards' shared
  budget. For durable, isolated parallel worktrees, follow
  [[FirstMate Integration Assessment]] instead.
- The task contract handed to a dispatched worker is a brief produced by
  `scripts/brief.py new` (Patrick's verbatim intent separated from the build
  spec). A brief that `python scripts/brief.py check <path>` rejects is not
  dispatched.

## Presets

| Preset | Sequence | Use when | Default authority |
|---|---|---|---|
| `prompt` | inspect → act → verify → report | One small, well-specified unit needs end-to-end tracing | R0/R1, named local scope |
| `scout` | inspect → report | You need reconnaissance, a comparison, or a bounded design report | R0, read-only |
| `plan` | inspect → plan → report | The intended change needs an implementation plan before a write | R0, read-only; T3 analysis for material ambiguity |
| `build` | inspect → act → verify → report | A narrow change is already understood | R1, named local paths |
| `quality` | inspect → deterministic checks → report | You need lint, format, schema, static, or focused mechanical evidence only | R0, read-only |
| `document` | inspect diff/source → write docs → verify → report | Accepted work needs concise documentation or a decision record | R1, named documentation paths |
| `plan-build` | plan → build → verify → report | A real but bounded change merits design before implementation | R1/R2, no implicit commit |
| `build-test` | build → focused test → bounded repair → report | A change needs executable proof at a stable public seam | R1/R2, named local paths |
| `build-review` | build → independent code review → bounded repair → report | Correctness of intent matters beyond automated checks | R1/R2; reviewer stays read-only |
| `full` | plan → build → quality → test → bounded repair → report | Default for a non-trivial, local change | R1/R2, no implicit commit |
| `full-quality` | plan → build → quality → test → review → bounded repair → report | A non-trivial change also needs independent review before handoff | R2 or high-consequence R1 |

`full` is the default when no preset is supplied and the task is a non-trivial
local change. Choose the narrowest preset that supplies the needed evidence;
adding stages without an acceptance reason is overhead, not safety.

## Model routing

[[AI Agent Workflow Standards#Appendix C — Claude Code mapping (2026-10-07)]]
owns the routing rules and [[Model Registry]] owns which model fills each tier.

| Stage | Tier |
|---|---|
| `scout` | T1; T1+ when the read needs judgment beyond a fixed plan; T3 when the question is architectural |
| `plan` | T2 for R1; T3 for R2 or any T3 trigger |
| `build`, `document` | T2 |
| `quality`, `test` | T0, run by T1; T1+ after the first failed T1 repair loop |
| `review` | T2 and never the builder; T3 for high-consequence R1 or R2 |
| verify, report | The coordinator (T3 in an interactive session) |

## Stage rules

### Scout and plan

Read the smallest authoritative surface and return a concise report in chat by
default. Do not create a vault note, change a task, or write a plan artifact
unless the task contract explicitly includes its path. A material architecture,
schema, privacy, security, migration, or hard-diagnosis decision requires the
read-only T3 seat before any mutation: Fable 5.1 on Claude Code (Appendix C of
[[AI Agent Workflow Standards]]), the `tars_high_assurance` role on Codex.

### Build and document

Preserve unrelated dirty work. Apply the smallest coherent change in the named
paths, then run the check declared in the task contract. For documentation,
distinguish verified facts from proposals and link internal source notes with
wikilinks. Mapped vault folders still require complete valid frontmatter; do not
use documentation work to bypass a schema rule.

### Quality, test, and review

`quality` runs deterministic gates appropriate to the affected surface. `test`
uses the highest stable public seam available; follow `/tdd` when an authorized
behaviour change needs durable regression coverage. `review` follows
`/code-review` across Contract, Spec, and Behaviour, with a reviewer that cannot
modify the surface. A finding reopens the build stage only within the original
write scope and repair budget; otherwise return an escalation packet.

### Completion and handoff

Return the result contract from [[AI Agent Workflow Standards#13. Result contract]],
including exact `pass`, `fail`, `not_run`, or `waived` evidence.
`not_run` and `waived` are never reported as passed. Report unknown cost or usage
as `null`, not zero. Do not call work complete until every mandatory criterion
passes, or an authorized waiver says exactly what remains waived.

## Status events

Every run emits status events via `scripts/tars_state.py`, so progress is
visible without reading the transcript:

- At start: `python scripts/tars_state.py open --kind adw --session <session id> [--task-uid <UID>]`.
  Capture the printed `run_id`.
- At each stage boundary:
  `python scripts/tars_state.py emit <run_id> working "<stage>"`.
- Waiting on the user:
  `python scripts/tars_state.py emit <run_id> needs-decision --key <key> "<reason>"`
  or `python scripts/tars_state.py emit <run_id> blocked "<reason>"`.
- At the end: `python scripts/tars_state.py emit <run_id> done "<evidence>"` or
  `python scripts/tars_state.py emit <run_id> failed "<evidence>"`.
- After any terminal event on a Task-linked run:
  `python scripts/tars_state.py progress <run_id> --write`. It no-ops safely on
  dr-fleet runs, so call it unconditionally.

Status events do not change the boundaries above. A failure to emit never
blocks the work (mirror A3-D4).

## Progress band

If the tool `mcp__tars-progress__progress` is available, keep the band above
the prompt and the agents pane current. Skip silently when it is absent. Call
it:

- after stating the task contract: `title` (a few words), `preset`, `stage`
  (the first stage), and, once worker tasks are known, `total` and `tasks`
  (`[{ title, tier, after }]` in dispatch order, `tier` as `T1`, `T2` or `T3`,
  `after` the numbers of the tasks a task waits for);
- at each stage boundary: `stage`;
- each time a worker result passes independent verification: `done`
  (accepted so far);
- when re-planning changes the tasks: the new `tasks` and `total`;
- once, with the result contract: `finished: true`.

Pass a task's `title` verbatim as the Agent tool `description` when
dispatching it, and again on a repair round, so the pane matches runs to
planned tasks.

Every dispatched brief carries this line for the worker: "If
`mcp__tars-progress__step` is among your tools, including as a deferred tool
(load it with ToolSearch `select:mcp__tars-progress__step`), call it right
after reading the brief with your plan's step count as `total` and `done: 0`,
then again with `done` and a few-word `note` as each step finishes. Skip
silently if the tool is absent."

Progress reports do not change the boundaries above. A failure to report never
blocks the work.

## Examples

```text
/adw scout map the guarded-push path and report concurrency hazards
/adw plan-build add a focused validation for the hook policy
/adw full-quality harden the scoped automation parser against malformed input
/adw document summarize the accepted change in Notes/ with its source links
```

Use `--commit` only with an explicit request such as:

```text
/adw full --commit add a focused validation for the hook policy
```

After a passing local commit, invoke `/safe-push` separately for the
fail-closed publish and PR path.
