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
workflow.

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

## Stage rules

### Scout and plan

Read the smallest authoritative surface and return a concise report in chat by
default. Do not create a vault note, change a task, or write a plan artifact
unless the task contract explicitly includes its path. A material architecture,
schema, privacy, security, migration, or hard-diagnosis decision requires the
read-only `tars_high_assurance` T3 role before any mutation.

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
