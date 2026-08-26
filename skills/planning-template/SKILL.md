---
name: planning-template
description: Design a client's master collection template with split potential and emit a build-ready spec plus a regenerable client plan. Six phases - intake, read-only scout, derive-then-confirm, design, challenge pass, emit. Stops at the tenant write boundary; never writes to a Datarails tenant. Use when the user says "design the <client> budget template", "spec the departmental template", "how should we split this planning template", "turn this workbook into a Datarails template", or hands over a client budget/forecast workbook and asks what to build.
---

# /planning-template

Turn a client's planning intent plus their existing budget/forecast workbook into a
**build-ready spec for one master collection template with split potential**.

**This skill designs and specifies. It never writes to a Datarails tenant.**
Build is a separate authority, requested separately, gated separately.

Out of scope: whole-planning-model strategy (dimension layer, driver engine,
scenario architecture). Those are different deliverables. If the ask is really
one of those, say so and stop.

---

## What you produce

| Artifact | Where | Nature |
|---|---|---|
| **The spec** | `Cowork/clients/<Client>/outputs/<cycle>-<descriptor>-Template-Spec.md` | durable source of truth; hand-maintained |
| **The client plan** | `Cowork/clients/<Client>/outputs/<cycle>-<descriptor>-Template-Plan-Client.md` | regenerable synthesis; cites the spec; **never hand-edited** |
| **MEMORY update** | `Cowork/clients/<Client>/MEMORY.md` | stable tenant facts only |
| **Build task** | `Tasks/` via **`/task`** | never hand-write a Task note |

Do **not** write a CRM dossier entry, do **not** run `/distill` (that is
`/knowledge-harvest`'s job), and do **not** append to `log.md` — its op
vocabulary is closed and none of these ops are in it.

---

## Phase 1 — Intake

### Mandatory input floor

Refuse to proceed without all three:

1. **Client** — resolves to `Cowork/clients/<X>/` and `CRM/Clients/<X>.md`.
2. **Server + tenant** — a `--server` key, confirmed with
   `dr whoami --server <key> [--account <email>]`. Echo the org back.
3. **One structural input** — their workbook, a mock-up, **or** a stated
   structure in words. Any one is enough; none is not.

Missing any of the three: stop and ask. This is the only hard block before the
scout.

### Read-only tenant interrogation is mandatory when the tenant exists

If the tenant exists, you interrogate it. There is no version of this workflow
that designs against an empty context when a populated one is one read away.

**On an empty or unpopulated tenant, PROCEED.** Do not stall. Every derived
answer that could not be checked becomes an entry in the spec's
**Unverified assumptions** block, and the corresponding challenge-pass check is
`not_run`.

### Name-collision check

Two clients can share a leading word (`Acme Health` vs
`Acme Brands`). Verify the email domain or the Salesforce account id against
`Cowork/clients/<X>/CLAUDE.md` before reading a single source file.

---

## Phase 2 — Read-only scout

All reads. Nothing here mutates anything. Run the tenant reads and the local
reads together; neither depends on the other.

### Local

1. `Cowork/os/knowledge/index.md` — the down step. Consult before building.
2. `Cowork/clients/<X>/MEMORY.md` — stable technical and tenant state.
3. `Cowork/clients/<X>/inputs/` and `outputs/` — prior art. A design note or
   game plan already there usually supersedes half of what you were about to
   derive.
4. **The workbook**, through the bundled inventory script:

```bash
python "<skill-dir>/workbook_inventory.py" "<path/to/workbook.xlsx>" --json
```

   It emits tabs, per-tab dimensions, hardcode-vs-formula ratio, named ranges,
   external links, and repeated-label columns as dimension candidates. It is
   deliberately thin — no formula extraction, no dependency graph. **Its
   header detection and its dimension candidates are heuristics and say so in
   their own output. Treat every candidate as a question for the tenant, never
   as an answer.**

   A high hardcode ratio on an input tab means the client types numbers there.
   A ratio near zero on a delivered template means it is formula-driven and its
   cost is call count, not typing. Both are design inputs.

### Tenant (read-only)

| Read | Answers |
|---|---|
| `dr templates list` | which table the template sources from |
| `dr templates get <tid>` | field names **and field IDs** — needed for split `--field` and range filters |
| `dr templates distinct <tid> --field "<name>"` | the exact split value set, exact strings |
| `dr templates aggregate <tid> --group-by <f> --metric <m>:SUM` | whether a dimension is populated, and history start |
| `dr dynamic-ranges list --table <tid>` | existing ranges, and how many the table already carries |
| `dr collection-processes list` | whether a CP already exists for this dimension |
| `dr functions list` / `dr reports list` | the function and scaffold for a Budget management master |
| `dr filebox list` | existing planning fileboxes and their tag config |

Wire mechanics for anything you are about to specify:
**`~/.claude/skills/dr-cli/reference/planning-templates.md`**. Read it before
the design phase, not after.

---

## Phase 3 — Derive then confirm

**Derive first. Propose every answer together with the evidence that produced
it. Ask the client to correct, not to supply.** A question asked cold that the
tenant could have answered is a defect in this workflow.

### Block on exactly four

Everything else is proposed-and-confirmed in one batch. These four stop the
workflow until answered:

**B1 — Split dimension and its value set.**
Irreversible: `collection-processes` has **no delete verb** and deletion is
UI-gated. A CP created on the wrong dimension cannot be removed from the CLI.
Propose the dimension and the full value list from `templates distinct`, with
counts. Get an explicit yes.

**B2 — Split mechanism.**
Collection process (workbook master) or document split (Budget management
master). Selection criteria and the reversibility asymmetry are in
`reference/planning-templates.md` §1. Propose one with the reason; confirm.

**B3 — Target cycle and scenario.**
Which planning cycle, which scenario. The scenario domain differs across the
three surfaces involved — check §6 of the reference before writing a value.

**B4 — Ownership.**
Who fills each child, and who administers the master. A template with no named
owner per child is a template nobody submits.

### Deferred, not asked: refresh strategy

**Roll-forward vs dynamic-range refresh is DEFERRED to the build phase.**
It is a performance and operating-effort call that requires a timing test
against a representative file, which a design-only workflow cannot run.

The spec must carry: a **stated recommendation**, the **tradeoff written down**,
and the **named file the build phase must test against** — the worst
representative one, not the convenient one. See
`Cowork/os/knowledge/runbooks/forecast-mapping-master-key-roll-forward.md`.

### Derived and confirmed — never asked cold

| Item | Derive from |
|---|---|
| split field distinct values | `templates distinct` |
| whether the dimension already exists | `templates aggregate` grouped by it — populated or not |
| history start month | `templates aggregate` by date, earliest period with the dimension populated |
| the mapper/filter the range must scope to | `templates distinct <tid> --field DataMapper_Name` + aggregate per mapper |
| input grain | workbook inventory + `templates sample` |
| actuals cutover | latest month with Actuals, clamped to before the current month |
| tag config | `collection-processes list --json` / `filebox get` |
| dynamic-range definition count vs instance count | `dynamic-ranges list --table <tid>` |

---

## Phase 4 — Design

Read before writing this phase, every time:

- `Cowork/os/knowledge/runbooks/forecast-mapping-master-key-roll-forward.md`
- `Cowork/os/knowledge/runbooks/fs-mapping-dynamic-lookup.md`

Design the master template: tab set, row keys, column bands, which columns are
input and which are derived, which row lists come from dynamic ranges and which
are baked, the join key, and the split boundary.

State the **range definition count** and, separately, the **instance count** the
chosen distribution produces. They are different numbers and only one of them
is what the tenant carries.

---

## Phase 5 — Challenge pass (MANDATORY)

**A spec is not shippable until this pass has run.** Every check reports
exactly one of:

| State | Meaning |
|---|---|
| `pass` | checked, and it holds |
| `fail` | checked, and it does not hold — fix the design or record it as a build blocker |
| `not_run` | **not checked.** State it. `not_run` is not `pass`. |
| `waived` | deliberately skipped with a named reason. `waived` is not `pass`. |

Every `not_run` on a tenant-dependent check feeds the spec's
**Unverified assumptions** block. An empty tenant legitimately produces many
`not_run`; that is an honest spec, not a failed one. What is not acceptable is
an unstated `not_run`.

### The catalog

Each check links to its source. **Read the linked page; do not work from the
one-line summary here.**

| # | Check | Failure it catches | Source |
|---|---|---|---|
| C1 | **Range / mapper scope** — does every range, seeding formula and BvA report carry the mapper filter? | N-times overstatement, no error anywhere | `Cowork/clients/<Client>/outputs/<cycle>-Template-Design-Note.md` §3.2 · same silent-multiplication class as [[stacked-block-repetitive-scan]] · **/distill candidate — no knowledge page yet** |
| C2 | **Submission-date window** — is any range filtered on a rolling date window? | member list silently empties weeks after each submit | [[dynamic-range-submission-date-window]] |
| C3 | **Definitions vs instances** — definition count stated separately from instance count? | range count that looks fine on paper and performs badly in the tenant | `reference/planning-templates.md` §7 · EBH design note §2.1 |
| C4 | **Join key** — is the join on a key that is unique across entities? | wrong-entity joins on bare account number | [[multi-entity-account-id-join]] |
| C5 | **Grain** — do all sources feeding this template share one grain? | mixed-grain double count | [[mapper-source-onboarding-guardrails]] |
| C6 | **Date regex / sheet filter** — will the mapper pick up the new tabs and periods? | new tab or period silently not ingested | [[mapper-source-onboarding-guardrails]] |
| C7 | **Sign convention** — is the sign of each measure verified at source? | every account double-counts or nets to zero | [[sap-tb-credit-presigned]] |
| C8 | **Empty scaffold** — is the module actually configured, or cloned and empty? | structural checks pass on a completely empty module | [[provisioned-scaffold-not-configured]] |
| C9 | **History start** — from which period is the split dimension actually populated? | blank comparatives discovered after go-live | EBH design note §3.3 |
| C10 | **Filter value strings** — does every filter value match the table exactly? | exact-match miss, e.g. `Operating Expense` singular, not `Operating Expenses` | `~/.claude/skills/dr-cli/reference/budget-builder.md` § Wire-shape gotchas |

C1, C2, C4, C5, C9 and C10 are checkable with read-only `dr` commands. Run them.
C3 is arithmetic on the design. C6, C7 and C8 may be `not_run` on a tenant that
has no feed yet — say so.

---

## Phase 6 — Emit

### 6.1 The spec

`Cowork/clients/<Client>/outputs/<cycle>-<descriptor>-Template-Spec.md`

```markdown
---
modified: <YYYY-MM-DDTHH:mm:ss-06:00>
---
# <Client> — <cycle> <descriptor> template spec

**Version:** <n> · <YYYY-MM-DD> · **Author:** <name>
**Tenant:** <server> / org <id> — read-only inspection, nothing written
**Structural input:** <workbook or mock-up path>

## 1. Decision summary
B1 split dimension · B2 mechanism · B3 cycle + scenario · B4 ownership —
each with the evidence that produced it.

## 2. Template structure
Tabs, row keys, column bands, input vs derived, range-driven vs baked.

## 3. Split design
Mechanism, dimension, exact value set, child naming, tag config, fill mode.

## 4. Dynamic ranges
Definition count AND instance count, per range: table, fields, filters
(field IDs), members today, new or existing.

## 5. Refresh strategy — DEFERRED to build
Recommendation, the tradeoff, and the named representative file the build
phase must performance-test against.

## 6. Challenge pass
C1–C10, one row each, exactly one of pass / fail / not_run / waived, with
the evidence or the reason.

## 7. Unverified assumptions
Every not_run and every derived-but-unconfirmed value. Explicit, not implied.

## 8. Build handoff
dr-cli-native command sequences + the exact JSON they consume.

## Sources
```

### 6.2 The build handoff (§8) — format

**dr-cli-native command sequences plus the exact JSON those commands consume**
(`--config-file`, `--template-file`, `--filters-json`, budget payloads).

- Field IDs resolved via `dr templates get`.
- Values confirmed via `dr templates distinct`.
- **No invented manifest schema.** If dr-cli has no flag for it, it does not go
  in the handoff as if it did.
- **Anything unresolvable is marked `UNRESOLVED`, never guessed.**
- **Emitting a command is NOT authorization to run it.** Two-step confirms and
  the prod desktop dialog stay intact. Say this in the spec.

### 6.3 The client plan

`Cowork/clients/<Client>/outputs/<cycle>-<descriptor>-Template-Plan-Client.md`

A separate, regenerable synthesis. It **cites the spec** and is **never
hand-edited** — edit the spec and regenerate. Lead with this header verbatim:

```markdown
> **Generated** from `<spec filename>` on <YYYY-MM-DD>. Do not edit this file —
> edit the spec and regenerate. Hand edits are lost on the next run.
```

Client-facing: what they get, what they fill, who owns which child, what is
still open, what we need from them. No field IDs, no CLI, no internal debt.

### 6.4 MEMORY.md

Append **stable tenant facts only** to `Cowork/clients/<X>/MEMORY.md` under
`## Facts`: template IDs, field IDs, the mapper the range must scope to,
whether the dimension already exists, history start. Date the subsection.

Not memory: the design itself, open questions, status, deadlines. Those live in
the spec and in PM state.

### 6.5 The build task

Delegate to **`/task`**. Never hand-write a Task note.

```
/task name: "<Client> - Build <descriptor> template"
      project: <the client's active engagement>
      phase: Model Builds
      priority: <as agreed>
```

Then add a Progress Note line pointing at the spec.

### 6.6 Close out

Run **`/lint`** after the batch of writes and confirm the new notes are clean.

---

## Rules

- **No tenant writes. Ever.** This skill's only `dr` verbs are reads.
- The spec is the source of truth; the client plan is generated from it.
- `not_run` is stated, never implied. `not_run` is not `pass`. `waived` is not
  `pass`. Report unknown counts as unknown, never as zero.
- Never edit `Bases/*.base`, `Administrator/`, `.obsidian/`, or the `tars-os`
  plugin.
- Never deliberately pull, stage, commit, push, or mutate git refs. Publication
  needs separate authority via `/safe-push`.
- Client work product stays under `Cowork/`; PM state stays in the vault.
