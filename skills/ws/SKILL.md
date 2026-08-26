---
name: ws
description: Log a work session in Work Sessions/ against an existing task and optionally a related Meeting. Live-call ledger sessions dispatch to the Meeting skill's idempotent helper; task work computes DurationMin and inherits project/company identity. Use when the user says "log a session", "log time", "I worked on <task>".
---

# /ws

Log a work session in `Work Sessions/` against an existing task or Meeting, per the
`session` fileClass (see `CLAUDE.md` § Schema contract → session). A session requires
at least one of `Task` or `Meeting`.

## Inputs

- **task** — fuzzy-match against `Tasks/*.md`. Required for build, admin, prep, and
  follow-up work. If supplied and it doesn't resolve, STOP.
- **meeting** — optional structured source/context link. For the Meeting's live-call
  session, this is required and creation must dispatch to
  `.claude/skills/meeting/ensure_session.py`; never hand-create a second call session.
- **start** — `YYYY-MM-DD HH:mm` (time required for sessions).
- **end** OR **duration** — provide one:
  - both start & end → `DurationMin` = whole minutes between them.
  - start & duration (minutes) → compute `EndTime = start + duration`.
- **hours-type** — `Billable` | `Non-billable` (default `Billable` for client work).
- **activity-type** — `Meeting` | `Build` | `Admin`.
- **audience** — `External` | `Internal`; derive from linked project/Meeting identity.
  Agent/heads-down work is `Build`; a live call is `Meeting`.

## Inherit, don't re-ask

Read the resolved task's frontmatter and carry over:
- `Task` = `"[[<task basename>]]"`
- `Project` = the task's `Project` value (already a `"[[...]]"` link)
- `Company` = the task's `Company`, or the project's `Company` if the task lacks it.

Only ask the human for these if they can't be derived.

If `Meeting` is supplied, use its resolved Project identity as a cross-check. A
conflict between task, Meeting, and project is an exception; do not guess. Derive
`ReportingBucket` from project/task identity, never `CallType`.

## Filename & frontmatter

Filename: **`<Client> - WS YYYY-MM-DD HHmm`** — `HHmm` with no colon in the
filename (e.g. `Acme - WS 2026-06-24 1656`). `<Client>` = the company short
name (match the task/project prefix). If that exact name exists, append ` (2)`.

```yaml
---
fileClass: session
Task: "[[<task>]]"
Meeting: "[[<meeting>]]"         # optional for task work; required for live calls
Project: "[[<project>]]"
Company: "[[<company>]]"
ReportingBucket: <Client Delivery|Internal Operations|TARS / OS>
HoursType: <Billable|Non-billable>
ActivityType: <Meeting|Build|Admin>
Audience: <External|Internal>
StartTime: <YYYY-MM-DD HH:mm>
EndTime: <YYYY-MM-DD HH:mm>
DurationMin: <int minutes>
ReclaimEventID:
tags:
  - session
modified: <YYYY-MM-DDTHH:mm:ss-06:00>
---
```

`Meeting` belongs in frontmatter. Do not create new body-only `Related call` links;
existing ones remain compatibility data until the physical migration.

## Dossier write-through

If the session shipped something **client-visible** (a deliverable, milestone, or
fix), APPEND one line to the client dossier's `## Timeline`
(`- YYYY-MM-DD — outcome ([[<this WS note>]])`). Routine heads-down build time does
**not** touch the dossier — only notable, client-visible outcomes. (Schema § 4.2.)

## Rules

- `StartTime`/`EndTime` keep the `HH:mm` colon in frontmatter; the filename uses `HHmm`.
- `DurationMin` is an integer count of minutes, no unit.
- Prep/follow-up may link both `Task` and `Meeting`, but uses `Build` or `Admin`.
  The one `ActivityType: Meeting` live-call ledger row is owned by the Meeting
  helper and is idempotent by Meeting/Gong source identity.
- After writing, run `/lint`. The session should appear in the task's
  `![[Work Sessions.base#By Task]]` embed.
