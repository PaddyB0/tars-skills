---
name: vault-schema
description: Load the TARS frontmatter contract (task, habit, scheduling_policy, project, milestone, session, meeting, crm_company, crm_contacts) before writing or editing frontmatter of any note in a mapped folder when no writer skill (/task, /ws, /meeting, /client-setup, /ingest-meeting) owns the write, or when a field outside that skill's template is touched.
---

# vault-schema

A note with a wrong enum value, a malformed key, or an empty-string date silently
disappears from every Base view. It is not an error the human will see. The note
just stops showing up on the board. Treat the field tables below as a contract,
not a guideline.

1. **Never create a note in a mapped folder without complete, valid frontmatter**
   per the tables below. A wrong enum silently vanishes the note from every Base view.
2. **Enum values are copy-paste exact** — including emoji, casing, and spacing.
3. **Dates: no empty strings.** Omit the value if unknown.

`Administrator/FileClasses/*.md` is the source of truth and wins over this file.
If they disagree, follow the fileClass. The field tables between the
`vault-schema:generated` markers are generated from the FileClasses and
`annotations.yaml` by `python scripts/build_vault_schema.py`; edit those inputs
and re-run it, never the tables. `--check` (AS7 in `/lint` pass 4) fails when
a table, a FileClass, or the lint `ENUMS` disagree, or `schema.json` is stale.

## Schema contract

Enum values are **copy-paste exact**, including emoji, spacing, and casing.
Every note carries `fileClass:` and a matching `tags:` entry. `modified:` is an
ISO timestamp with offset (`2026-07-02T14:14:58-06:00`); `created:` is `YYYY-MM-DD`.

### task — `Tasks/` · `fileClass: task` · `tags: [task]`

<!-- vault-schema:generated fileclass=task -->
| Field | Type | Values / format |
|---|---|---|
| `Status` | Select | `⚫ BACKLOG` · `⚪ TO DO` · `🔵 IN PROGRESS` · `🟣 HUMAN REVIEW` · `🟠 REWORK` · `🟢 MERGING` · `🟢 COMPLETE` · `⚫ CANCELED` · `⚫ DUPLICATE` |
| `Priority` | Select | `Low` · `Medium` · `High` · `Critical` |
| `Phase` | Select | `Kick-Off` · `Change Planning` · `Workspace Configuration` · `Model Builds` · `Dashboard Design` · `Training + Enablement` |
| `Visibility` | Select | `client facing` · `internal` |
| `Project` | File | quoted wikilink → `Project: "[[Acme - PS Q2 2026]]"` |
| `Milestone` | File | optional quoted wikilink to a milestone whose `Project` matches the task |
| `Parent` | File | quoted wikilink (parent task) |
| `BlockedBy` | MultiFile | list of quoted wikilinks; empty = `[]` |
| `Meeting` | File | quoted wikilink to the source meeting note; used for meeting action items |
| `Company` / `Contact` | File | quoted wikilink |
| `Assignee` | File | quoted wikilink |
| `Executor` | Select | `Patrick` · `Code-Mac` · `Code-Win` · `Code-Work` · `Cowork` — task routing; empty = Patrick |
| `Workflow` | Select | `dr-recon` · `dr-lut-diagnose` — dr-fleet workflow queued for the machine in `Executor`; the dispatcher moves the task `⚪ TO DO` → `🔵 IN PROGRESS` → `🟣 HUMAN REVIEW`; omit when none |
| `SyncToReclaim` | Boolean | `true` or absent; Reclaim push opt-in gate |
| `ReclaimTaskID` | Input | numeric string; Reclaim push idempotency |
| `UID` | Input | immutable UUIDv4; required for new Tasks and before `AutoSchedule: true`; legacy Tasks may omit |
| `AutoSchedule` | Boolean | `true` or absent; explicit TARS scheduling opt-in; cannot coexist with `SyncToReclaim: true` |
| `ScheduleMode` | Select | `flexible` · `fixed` · `manual`; new Tasks default to `manual`; opted-in Tasks must be `flexible` |
| `MinBlockMin` / `MaxBlockMin` | Number | optional positive-integer minute overrides; when both exist, minimum must not exceed maximum |
| `SchedulingPolicy` | File | optional quoted wikilink to a `scheduling_policy`; required for `AutoSchedule: true` |
| `Energy` | Select | `deep` · `shallow` · `any` |
| `Repeat` | Select | `daily` · `weekly` · `monthly` · `yearly` |
| `RepeatUntil` | Date | `YYYY-MM-DD`; omit if open-ended |
| `StartDate` / `DueDate` | DateTime | `YYYY-MM-DD` or `YYYY-MM-DD HH:mm` — **never `""`; omit the value if unknown** |
| `Estimate` | Number | hours (number, no unit) |
| `Description` | Input | short text |
| `Sessions` | File | back-reference (usually left empty; the WS note links up) |
| `Completed_At` | Formula | auto — set only when `Status: 🟢 COMPLETE`; `⚫ CANCELED` and `⚫ DUPLICATE` are closed but not completed; you may write it directly as `YYYY-MM-DD HH:mm` |
<!-- /vault-schema:generated -->

Body scaffold (mirrors the template, minus interactive `INPUT[...]` meta-bind widgets — keep those lines if present; they render for the human):

```markdown
### Description

### Progress Notes

### Time tracking

![[Work Sessions.base#By Task]]
```

Naming: `<Client> - <Descriptor>` (e.g. `Acme - Budget Templates`).

Scheduling fields do not change Task intent semantics. `StartDate` remains “not
before,” `DueDate` remains the deadline, and neither field mirrors a placed calendar
block. A legacy Task without `UID` remains schema-valid. A recurring Task successor
must receive a fresh `UID`; scheduling preferences may carry forward, but provider
identity must not.

### habit — `Habits/` · `fileClass: habit` · `tags: [habit]`

<!-- vault-schema:generated fileclass=habit -->
| Field | Type | Values / format |
|---|---|---|
| `UID` | Input | immutable UUIDv4; required while active |
| `Status` | Select | `active` · `paused` · `retired` |
| `Priority` | Select | `Low` · `Medium` · `High` · `Critical` |
| `Cadence` | Select | `daily` · `weekly` |
| `TargetCount` | Number | positive integer occurrences per cadence period |
| `DaysOfWeek` | Multi | `monday` · `tuesday` · `wednesday` · `thursday` · `friday` · `saturday` · `sunday`; required for an active weekly Habit |
| `DurationMin` | Number | positive integer minutes per occurrence |
| `EarliestTime` / `PreferredTime` / `LatestTime` | Input | `HH:mm`; an active Habit requires earliest and latest, with optional preferred inside that range |
| `SchedulingPolicy` | File | quoted wikilink to exactly one `scheduling_policy`; required while active |
| `CatchUpPolicy` | Select | `skip` · `rollover-once` · `catch-up-capped` |
| `CalendarVisibility` | Select | `default` · `private` |
| `StartDate` / `EndDate` | Date | optional inclusive `YYYY-MM-DD`; start must not follow end |
| `Description` | Input | short text |
<!-- /vault-schema:generated -->

A Habit is a flexible work rule, not a recurring Task and not proof of actual work.
New Habit templates start `paused`; activate only after cadence, duration, time
window, and policy are complete.

### scheduling_policy — `Scheduling Policies/` · `fileClass: scheduling_policy` · `tags: [scheduling_policy]`

<!-- vault-schema:generated fileclass=scheduling_policy -->
| Field | Type | Values / format |
|---|---|---|
| `UID` | Input | immutable UUIDv4 |
| `Timezone` | Input | IANA timezone, e.g. `America/Edmonton` |
| `MondayWindow` … `SundayWindow` | Input | optional `HH:mm-HH:mm`; at least one work window is required and start must precede end |
| `MeetingWindow` | Input | optional `HH:mm-HH:mm` |
| `NoMeetingWindows` | Input | optional free scalar operating note; Phase 2 does not interpret it |
| `DeepWorkWindow` / `ShallowWorkWindow` | Input | optional recurring policy-local `HH:mm-HH:mm` energy preferences; each is clipped to that day's hard work window and never expands eligibility |
| `NormalHoursWindow` | Input | optional recurring policy-local `HH:mm-HH:mm` preference; eligible minutes outside it remain feasible but rank last |
| `DefaultTaskMinBlockMin` / `DefaultTaskMaxBlockMin` | Number | positive integer minutes; minimum must not exceed maximum |
| `DefaultHabitDurationMin` | Number | positive integer minutes |
| `DailyCapacityMin` / `WeeklyCapacityMin` | Number | positive integer minutes |
| `MeetingPrepMin` / `TravelBufferMin` / `DecompressionMin` / `WorkBreakMin` | Number | nonnegative integer minutes |
| `SoftFreezeHours` / `HardLockHours` | Number | nonnegative integer hours; hard lock must not exceed soft freeze |
| `TargetCalendar` | Input | required logical target calendar name |
| `DefaultVisibility` | Select | `default` · `private` |
| `ApplyMode` | Select | `assisted` · `automatic` |
| `Description` | Input | short text |
<!-- /vault-schema:generated -->

Scheduling Policy frontmatter stays flat so FileClass, lint, agent hooks, and TARS OS
all parse the same contract. Policy notes contain no provider credential, calendar
token, event ID, or attendee data. Preference windows are optional, same-day scalar
values: omit an unused key. A present blank value, list, malformed window, or
overnight range is invalid. Missing `NormalHoursWindow` makes every hard-eligible
minute normal; missing matching energy preferences and Task `Energy: any` are
neutral. Deep and shallow windows may overlap.

### project — `Projects/` · `fileClass: project` · `tags: [project]`

<!-- vault-schema:generated fileclass=project -->
| Field | Type | Values / format |
|---|---|---|
| `Status` | Select | `🟠 backlog` · `⚪ planned` · `🔵 active` · `🔴 at risk` · `🟢 complete` |
| `Type` | Select | `Premium Success` · `CS Hours` · `AI Transformation Services` |
| `Company` | File | quoted wikilink |
| `Contacts` | MultiFile | list of quoted wikilinks |
| `ScopeCategory` | Select | `40+ hrs` · `26-39 hrs` · `11-25 hrs` · `0-10 hrs` |
| `Scope_hrs` | Number | contracted hours |
| `HubIcon` | Select | `rocket` · `folder-kanban` · `briefcase-business` · `chart-no-axes-column` · `building-2` · `target` · `sparkles` · `wrench`; omit for deterministic fallback |
| `HubColor` | Select | `blue` · `green` · `purple` · `cyan` · `orange` · `pink` · `yellow` · `red`; omit for deterministic fallback |
| `BonusAssignedAt` / `BonusLiveAt` | Date | `YYYY-MM-DD`; explicit earned-bonus events, omitted until earned |
| `StartTime` / `EndTime` | DateTime | `YYYY-MM-DD` or `YYYY-MM-DD HH:mm` |
| `Completed_at` | Formula | Formula field with no formula defined in the FileClass; nothing sets it; omit |
| `sf.ProjectName` | Input | Salesforce project name |
| `sf.NotetoSETeam` | Input | free text |
<!-- /vault-schema:generated -->

Body: `## Overview`, `## Tasks` (a ` ```base ` block filtering `Project == this.file`), `## Meeting Log`, `## Hours Log`.
Naming: `<Client> - <Type abbrev> Q# YYYY` (e.g. `Acme - PS Q2 2026`).

Project lifecycle semantics are centralized: Backlog is parked/uncommitted and
non-terminal; Planned is committed but not started; Active and At risk are current
delivery; Complete is the only terminal status. Only Active and At risk participate
in active routing, active-hours burn, and recurring bonus eligibility. A project is
archived when Complete or physically under `Projects/Complete/`.

### milestone — `Milestones/` · `fileClass: milestone` · `tags: [milestone]`

<!-- vault-schema:generated fileclass=milestone -->
| Field | Type | Values / format |
|---|---|---|
| `Project` | File | required quoted wikilink to a project |
| `TargetDate` | Date | optional `YYYY-MM-DD`; omit when unknown |
| `Description` | Input | optional short text |
| `Completed_At` | DateTime | explicit completion timestamp `YYYY-MM-DD HH:mm`; omit while open |
<!-- /vault-schema:generated -->

Naming: `<Project> - MS - <Milestone name>`. Milestone progress is derived from
tasks whose optional `Milestone` link resolves to it. The milestone and linked
tasks must resolve to the same project. Completion is explicit; reopening removes
`Completed_At`. Recurring task successors clear `Milestone` by default.

### session — `Work Sessions/` · `fileClass: session` · `tags: [session]`

<!-- vault-schema:generated fileclass=session -->
| Field | Type | Values / format |
|---|---|---|
| `Task` | File | quoted wikilink to the task; optional when `Meeting` exists |
| `Meeting` | File | quoted wikilink to the source Meeting; a session requires at least `Task` or `Meeting` |
| `Project` | File | quoted wikilink to the project |
| `Company` | File | quoted wikilink |
| `ReportingBucket` | Select | `Client Delivery` · `Internal Operations` · `TARS / OS` — required when classifiable; derive from project/task identity, never `CallType` |
| `HoursType` | Select | `Billable` · `Non-billable` |
| `ActivityType` | Select | `Meeting` · `Build` · `Admin` |
| `Audience` | Select | `External` · `Internal` |
| `StartTime` / `EndTime` | DateTime | **`YYYY-MM-DD HH:mm`** (time required) |
| `DurationMin` | Number | exact minutes = (`EndTime` − `StartTime`) |
| `ReclaimEventID` | Input | usually empty |
<!-- /vault-schema:generated -->

`ActivityType`, `Audience`, and `HoursType` are independent dimensions: a client
call is `Meeting` + `External` + `Billable`; an internal call is `Meeting` +
`Internal` + `Non-billable`; agent work is `Build` with audience derived from the
linked project identity. Session does not inherit the task schema.

Naming: **`<Client> - WS YYYY-MM-DD HHmm`** (note: `HHmm`, no colon, in the filename;
the `StartTime` frontmatter keeps the `HH:mm` colon).

### meeting — `Meetings/` · `fileClass: meeting` · `tags: [meeting]`

<!-- vault-schema:generated fileclass=meeting -->
| Field | Type | Values / format |
|---|---|---|
| `Company` | File | quoted wikilink |
| `Contacts` | MultiFile | list of quoted wikilinks; empty = `[]` |
| `Project` | File | quoted wikilink |
| `ReportingBucket` | Select | `Client Delivery` · `Internal Operations` · `TARS / OS` — required when classifiable; derive from `Project`, never `CallType` |
| `CallType` | Select | `internal call` · `external call` |
| `CallUrl` | Input | Gong/meeting URL |
| `GongId` | Input | Gong call id (quote if numeric) |
| `GongTitle` | Input | cleaned Gong notification subject; optional legacy records may omit it. Inferred Calendar/Gong joins require either exact normalized title evidence or the constrained `<client> <> Datarails | <descriptor>` ↔ `<client> -- Datarails - <descriptor>` separator equivalence. External structured titles must resolve exactly one reciprocal CRM Company/Project by company name or explicit `GongTitleAliases`; any attendee that resolves in CRM must agree |
| `GongReceivedAt` | DateTime | `YYYY-MM-DD HH:mm`; Gmail receipt time for correlation only, never the meeting start |
| `GongDurationMin` | Number | positive Gong-reported call duration; authoritative for linked live-call Meeting/Work Session duration, anchored at Calendar `StartTime` |
| `ZoomMeetingUUID` | Input | quoted Zoom recording instance UUID; written by `/ingest-meeting` only when it authored the body from that Zoom transcript (raw transcript in gitignored `Transcripts/<meeting basename>.md`). Absent = body is Gong-sourced or hand-written |
| `CalendarProvider` | Select | `reclaim` · `google` · `outlook`; present only when explicitly linked/promoted from a calendar event |
| `CalendarEventID` | Input | provider occurrence ID; paired with `CalendarProvider` as the durable calendar join key |
| `Passcode` | Input | usually empty |
| `StartTime` / `EndTime` | DateTime | `YYYY-MM-DD HH:mm` |
| `IngestedAt` | DateTime | `YYYY-MM-DD HH:mm` — set **after** `/ingest-meeting` propagation completes, never before. **Omit until then** (empty = not ingested; never `""`) |
<!-- /vault-schema:generated -->

Body: `## Recap`, `## Key Points`, `## Next Steps`.
Naming: **`<Client> - <Kind> (YYYY-MM-DD)`** (e.g. `Acme - Call (2026-06-24)`,
`Acme - Sync 3 (2026-05-11)`). When `StartTime` is present, the date in the
filename **must** match it. An unlinked Gong source has no `StartTime`; its filename
date follows `GongReceivedAt` until explicit reconciliation.

### crm_company — `CRM/Clients/` · `fileClass: crm_company` · `tags: [crm_company]`

<!-- vault-schema:generated fileclass=crm_company -->
| Field | Type | Values / format |
|---|---|---|
| `Type` | Select | `Company` · `Contact` |
| `Industry` / `SubIndustry` | Multi | list of strings |
| `Timezone` | Select | `EST` · `PST` · `MST` · `CDT` |
| `BillingAddress` | Input | free text |
| `sf.Url` | Input | Salesforce account URL |
| `Project` | File | quoted wikilink |
| `ContactName` | MultiFile | list of quoted wikilinks to contacts |
| `GongTitleAliases` | Multi | optional explicit client-title aliases used only by the constrained Gong/Calendar separator-equivalence join; exact normalized token equality is required |
| `DossierUpdated` | Date | `YYYY-MM-DD` — last propagation touch to the dossier body. Omit until first ingest |
<!-- /vault-schema:generated -->

Naming: the company name (e.g. `Acme`).

### crm_contacts — `CRM/Contacts/` · `fileClass: crm_contacts` · `tags: [crm_contact]` · **extends `crm_company`**

> ⚠️ **Naming trap:** the fileClass filename is `crm_contacts` (**plural**) but its
> tag is `crm_contact` (**singular**). Notes MUST use `fileClass: crm_contacts` and
> `tags: [crm_contact]`. (The stock template ships with `fileClass: crm_contact` —
> that is wrong; use the plural.)

<!-- vault-schema:generated fileclass=crm_contacts -->
| Field | Type | Values / format |
|---|---|---|
| `contact.recordtype` | Select | `Decision Maker` · `Champion` · `Contact` |
| `contact.title` | Input | job title |
| `contact.email` | Input | email |
| `Company` | File | quoted wikilink |
| `Type` | Select (inherited) | `Company` · `Contact`; contact notes always use `Contact` |
| `Timezone` | Select (inherited) | `EST` · `PST` · `MST` · `CDT` |
| `GongTitleAliases` | Multi (inherited) | inherited from `crm_company` (not in `excludes`); see the `crm_company` row |
| `DossierUpdated` | Date (inherited) | inherited from `crm_company` (not in `excludes`); see the `crm_company` row |
<!-- /vault-schema:generated -->

Naming: the person's name (e.g. `Riley Novak`).

## Conventions

- **Quoted wikilinks in frontmatter:** single-file links are quoted — `Company: "[[Acme]]"`.
  Multi-file / list links use a YAML block list of quoted links:
  ```yaml
  Contacts:
    - "[[Riley Novak]]"
  ```
  An empty multi-file field is `[]`; an empty single field is the key with no value.
- **Dates:** `YYYY-MM-DD` for date-only fields, `YYYY-MM-DD HH:mm` for datetime.
  **Never write `""` for a date** — Base date filters treat `""` as unparseable
  (not absent), which breaks the view. Omit the value instead.
- **Wikilink targets must resolve** to a real note basename in the vault.
- **Scheduler ownership:** `AutoSchedule: true` and `SyncToReclaim: true` are
  mutually exclusive. Flip ownership deliberately by cohort; retaining an old
  `ReclaimTaskID` after Reclaim opt-out is allowed as migration evidence.
- **Scheduler UIDs:** UUIDv4 values are immutable. Never reuse a Task or Habit UID
  for a recurring successor or a different note.
- **`ReportingBucket`** is a reporting dimension, not client identity: client
  engagement project → `Client Delivery`; `Datarails Ongoing` →
  `Internal Operations`; TARS project/task → `TARS / OS`. Leave a legacy record
  unclassified and surface it in `Activities.base#Exceptions` rather than inventing
  an `Other` value or a synthetic internal company.
- **Migration-only duplicate flag:** `duplicate/meeting-source` is an extra tag,
  not a target property. It marks verified Notion-imported Meeting duplicates for
  deletion; Activities Exceptions surfaces them, duration reporting excludes them,
  and the Meeting ledger helper must never reuse them as authoritative rows.

