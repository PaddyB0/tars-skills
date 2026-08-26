---
name: task
description: Create a schema-valid task note in Tasks/. Args - name, project, due, priority, phase. Resolves the project wikilink or refuses to write. Writes full frontmatter + body scaffold. Use when the user says "create a task", "add a to-do", "new task for <client>".
---

# /task

Create a task note in `Tasks/` with complete, valid frontmatter per the `task`
fileClass (see `CLAUDE.md` § Schema contract → task).

## Inputs (ask only for what's missing)

- **name** (required) — task title. Filename convention: `<Client> - <Descriptor>`.
- **project** — fuzzy-match against `Projects/*.md`. Take the argument, list the
  project basenames (`Projects/`), and pick the best match. **If no project link
  resolves, STOP and ask** — do not write a task with a dangling `Project` link.
- **due** — `YYYY-MM-DD` (or with `HH:mm`). Omit the value if unknown; never `""`.
- **priority** — `Low` | `Medium` | `High` | `Critical` (default `Medium`).
- **phase** — one of: `Kick-Off`, `Change Planning`, `Workspace Configuration`,
  `Model Builds`, `Dashboard Design`, `Training + Enablement` (default `Kick-Off`).
- **visibility** — `client facing` | `internal` (default `client facing`).

Infer `Company` from the resolved project's `Company` frontmatter when present.
Generate a fresh UUIDv4 for every new Task. New Tasks begin with
`ScheduleMode: manual` and no `AutoSchedule` opt-in.

## Frontmatter to write

```yaml
---
fileClass: task
UID: <fresh UUIDv4>
Status: ⚪ TO DO
Priority: <Medium|...>
Phase: <phase>
Visibility: <client facing|internal>
Project: "[[<resolved project basename>]]"
Company: "[[<company>]]"        # if known from the project; else omit
StartDate: <YYYY-MM-DD HH:mm>   # now, or omit
DueDate: <YYYY-MM-DD>           # or omit the value entirely — never ""
Estimate:                       # number of hours, or leave empty
AutoSchedule:                   # absent/empty until explicit TARS opt-in
ScheduleMode: manual
MinBlockMin:
MaxBlockMin:
SchedulingPolicy:
Energy:
Parent:
BlockedBy: []
Assignee:
Description:
Sessions:
Completed_At:
created: <YYYY-MM-DD>
modified: <YYYY-MM-DDTHH:mm:ss-06:00>
tags:
  - task
---
```

## Body scaffold

```markdown
### Description

### Progress Notes

### Time tracking

![[Work Sessions.base#By Task]]
```

## Rules

- Enum values copy-paste exact (emoji included). A wrong enum vanishes the note
  from every Base view.
- Dates: `YYYY-MM-DD` or `YYYY-MM-DD HH:mm`. Omit unknown dates — no `""`.
- `AutoSchedule: true` is valid only with a UUID, `ScheduleMode: flexible`, a
  resolving `SchedulingPolicy`, valid optional block bounds, and no
  `SyncToReclaim: true`.
- Legacy Tasks without `UID` remain valid, but every Task created by this skill
  receives one. Never copy a UID to a recurring successor.
- Do **not** run the Templater template in `Administrator/Templates/` — it's
  interactive. Write the frontmatter directly.
- After writing, run `/lint` and confirm the new note is error-free.
