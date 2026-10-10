---
name: meeting
description: Create a meeting note in Meetings/, link its company/project/contacts, and idempotently ensure exactly one authoritative live-call Work Session. Optionally ingest a transcript into Recap/Key Points/Next Steps and offer action items as /task creations. Use when the user says "log a meeting", "meeting notes", "here's the transcript from <call>".
---

# /meeting

Create a meeting note in `Meetings/` per the `meeting` fileClass (see the
`vault-schema` skill → meeting).

## Inputs

- **client / company** (required) — resolve to a `CRM/Clients/` note.
- **kind** — `Call`, `Sync N`, `Kick-Off`, etc. (goes in the filename).
- **date** — `YYYY-MM-DD`; **must** match `StartTime`'s date.
- **start / end** — `YYYY-MM-DD HH:mm`.
- **call-type** — `internal call` | `external call`. A meeting with a client is
  `external call`; an internal team meeting is `internal call`. (Do not write
  `client call` — that is not a valid enum value.)
- **project** — resolve to a `Projects/` note when the meeting is engagement work.
- **contacts** — resolve to `CRM/Contacts/` notes.
- **transcript** (optional) — pasted text to summarize.
- **calendar provider / event ID** (optional, paired) — only when an explicit
  calendar link or promotion supplies a provider occurrence identity. Supported
  providers: `reclaim` · `google` · `outlook`.

Derive `ReportingBucket` from the resolved project identity per `vault-schema` →
Conventions. If the project cannot be classified, stop and surface the Meeting as
an exception.

## Filename & frontmatter

Filename: **`<Client> - <Kind> (YYYY-MM-DD)`** (e.g. `Acme - Call (2026-06-24)`).

Load `/vault-schema` for the `meeting` fileClass fields and enum values before
writing. This skill sets `fileClass: meeting` and these fields: `tags`, `Company`,
`Contacts`, `Project`, `ReportingBucket`, `CallType`, `CallUrl`, `GongId` (quote
when numeric), `CalendarProvider` and `CalendarEventID` (paired; the occurrence
id, not the series id), `Passcode`, `StartTime`, `EndTime`.

## Body

```markdown
## Recap

## Key Points

## Next Steps
```

If a transcript is provided: write a short **Recap**, group substance under
**Key Points** with `###` subheadings, and list concrete owner-prefixed items
under **Next Steps** (e.g. "Patrick to …", "<Contact> to …").

## Action items → tasks

After summarizing, surface the Next Steps that belong to Patrick and **offer** to
create them via `/task` (linked to the same project). Don't auto-create — confirm
first.

## Authoritative ledger session — create immediately and idempotently

After writing the Meeting, run the canonical helper from the vault root:

```bash
python3 .claude/skills/meeting/ensure_session.py "Meetings/<meeting filename>.md"
```

This is part of Meeting creation, not an optional `/ws` offer. The helper:

- finds the existing live-call Work Session by structured `Meeting` link first,
  by the linked Meeting's `GongId` second, and by a constrained time/project/company
  fallback only for non-Gong Meetings;
- ignores any migration-only `duplicate/meeting-source` deletion candidate so an
  imported duplicate can never be promoted to the authoritative ledger row;
- reuses one match, errors visibly on multiple matches, and creates only when none
  exists;
- seeds a new session's `StartTime` / `EndTime` and exact `DurationMin` from the
  Meeting, links `Meeting` in frontmatter, and derives `Project`, `Company`,
  and `ReportingBucket` from the linked project;
- never rewrites an existing Work Session's ledger timing. A Meeting/ledger timing
  mismatch is an exception warning; raw Meeting timestamps also remain unchanged.

The helper writes `ActivityType: Meeting` plus derived `Audience`; linked
`Build`/`Admin` sessions remain prep/follow-up, not the Meeting's one live-call
ledger session. Re-running this step must report `REUSED`,
not create another live-call session.

### Live-call ledger contract

Exactly one `ActivityType: Meeting` ledger row may represent a Meeting source. For
a calendar-linked Gong Meeting, Calendar supplies the `StartTime` anchor and
positive `GongDurationMin` is authoritative for live-call duration:
`EndTime = StartTime + GongDurationMin`, and the Work Session mirrors those
timestamps and exact duration. Unlinked Gong receipt metadata never invents timing.
An existing Gong-owned Session may be surgically reconciled only when its identity
is valid and its timing matches either the prior Calendar window or the target Gong
window; other disagreements remain visible exceptions. Reporting reads Work
Sessions.

Gong and Calendar join fields (`GongTitle`, `GongTitleAliases`, `GongReceivedAt`,
`GongDurationMin`, `CalendarProvider` + `CalendarEventID`) are defined in
`vault-schema` → meeting and crm_company.

### Internal-only Gong route

For Gong receipts whose Calendar attendees are exclusively `@datarails.com`,
the sole allowed internal ledger route is `Project: [[Datarails Ongoing]]`, no
synthetic Company, `ReportingBucket: Internal Operations`, `CallType: internal
call`, and one `Internal` / `Non-billable` Meeting Work Session.

## Hand off to ingest ("file, then ingest")

`/meeting` files the note and ensures its ledger session; it does not propagate the
wiki layer. A meeting is not "done" until ingested. After writing (and any offered
`/task`), **offer to run `/ingest-meeting` on this note** so it propagates to the
dossier, person pages,
project Meeting Log, and Tasks, and gets stamped `IngestedAt`.

> Meetings that arrive automatically (Gong → vault) never pass through here — the
> same helper runs as the first durable step of `/ingest-meeting`. The `IngestedAt`
> backlog remains owned by `/catchup` and the daily scheduled check.

## Rules

- The date in the filename must equal `StartTime`'s date.
- `CalendarProvider` and `CalendarEventID` are optional but atomic: write both or
  neither, and never reuse their pair on another Meeting note.
- `CallType` is one Select scalar from the enum, not a YAML list.
- Do not stamp or hand off a newly created Meeting as complete unless the helper
  created or reused exactly one live-call ledger session.
- After writing, run `/lint`.
