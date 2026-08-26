---
name: ingest-meeting
description: Ensure one authoritative live-call Work Session, then propagate a meeting into the wiki — fill Contacts, update the dossier, person pages, project Meeting Log, and Tasks, log it, then stamp IngestedAt last. This is the core Unified-OS loop. Use when the user says "ingest this meeting", "process the backlog", or after /meeting files a note. Default target = every Meetings/ note with empty IngestedAt, oldest first.
---

# /ingest-meeting [note]

The core propagation loop: **one meeting → ~10 pages**, exactly once, idempotent.
Spec: [[TARS Unified OS - Schema]] § 4.1 (propagation matrix) and § 5 (op contract).
This is the highest-leverage operation in the OS — a meeting is not "done" until
ingested, and the backlog is every `Meetings/` note with an empty `IngestedAt`.

## Target selection

- **No argument** → every `Meetings/*.md` where `IngestedAt` is empty, **oldest
  `StartTime` first**. Process one at a time; re-read state between meetings.
- **Argument** → fuzzy-match one meeting note and ingest just that one.
- **Internal meeting** (no `Company`, e.g. TAM notes) → skip client dossier/person
  writes. It still needs a classifiable linked project for a new ledger session;
  colleagues never become CRM contacts.

## Steps (in order — the stamp is always last)

### 0 · Require a knowledge-ready source
- Before any write, a Gong-owned Meeting (`GongId` present) must contain
  substantive content in at least one of `## Recap`, `## Key Points`, or
  `## Next Steps` beyond the importer scaffold and any calendar-review marker.
- If all three sections are empty/placeholders, **STOP** before the Work Session,
  propagation, task, log, or `IngestedAt` writes. Report that Gong enrichment is
  still pending; ingestion must never turn an empty receipt into authoritative
  wiki state.
- `/ingest-meeting` never fills the raw Meeting body. Only the importer may perform
  the authorized one-time transition from an un-ingested exact Gong placeholder to
  the allowlisted Gong-generated body for the same `GongId`.

### 1 · Normalize meeting frontmatter
- Read the meeting body. Fill `Contacts:` from attendees **named in the body**,
  as a YAML block list of quoted wikilinks.
- For each named attendee with no page in `CRM/Contacts/`, **create one** —
  schema-exact: `fileClass: crm_contacts` (plural), `tags: [crm_contact]`
  (singular), `Company` set, person-page scaffold (§ 3.2: `## Profile` ·
  `## Working notes` · `## Open threads` · `## Timeline`). People known only by
  first name stay **plain text with "(no page yet)"** — never fabricate a page (G2).
- Confirm `Project`; fallback = the company's current active engagement.
- Derive and set `ReportingBucket` from that Project (`Client Delivery`,
  `Datarails Ongoing` → `Internal Operations`, TARS / Unified OS → `TARS / OS`).
  Never use `CallType`, `Other`, or a synthetic company.
- **Do not touch the meeting body** — it is an immutable raw source.

### 2 · Ensure the authoritative live-call Work Session

For every Meeting on or after the duration-reporting cutoff (`2026-06-01`), run
this before any propagation writes:

```bash
python3 .claude/skills/meeting/ensure_session.py "Meetings/<meeting filename>.md"
```

`CREATED` and `REUSED` both satisfy the step. Multiple matches, missing post-cutoff
timing, an unclassifiable Project, or conflicting identity are visible exceptions:
stop before propagation and do not stamp `IngestedAt`. Do not rewrite Meeting
timestamps or existing Work Session ledger timing to reconcile a mismatch.
The helper ignores Work Sessions tagged `duplicate/meeting-source`; those are
staged deletion candidates, not authoritative rows.

Pre-cutoff Meetings remain eligible for activity/count ingestion but do not create
duration ledger rows unless an explicit historical backfill is requested.

### 3 · Client dossier (`CRM/Clients/<Company>.md` body)
- `## Snapshot` — REWRITE only if engagement state changed (present tense, 2–6 sentences).
- `## Commitments & open loops` — CHECKLIST delta from Next Steps, **both directions**
  (We owe them / They owe us). **Client-owed steps live here, never as Tasks.**
- `## Timeline` — APPEND **one** line, newest first:
  `- YYYY-MM-DD — one-liner ([[<meeting basename>]])`. A material contradiction
  with an earlier claim gets a `⚠️` prefix line — never a silent overwrite.
- Set frontmatter `DossierUpdated: YYYY-MM-DD`.

### 4 · Person pages (attendees)
- `## Timeline` APPEND one line; `## Profile` / `## Working notes` MERGE only where
  the call revealed something new.

### 5 · Project note (`## Meeting Log`)
- APPEND `- YYYY-MM-DD — [[<meeting note>]] — one-line outcome`.

### 6 · Tasks
- Each **Patrick-owned, actionable** Next Step → dedupe against open tasks (same
  `Project`, similar descriptor).
  - **Hit** → append a Progress Notes line: `- YYYY-MM-DD — carried in [[<meeting>]]`.
  - **Miss** → create a task via the `/task` contract: `Status: ⚪ TO DO`, `Project`,
    `Company`, `Description` **ending with the source link**. Dates/priority only if
    stated in the meeting — **never invented**.
- **Client-owed steps → dossier checklist (step 3), never Tasks.**

### 7 · OS log (`log.md` at vault root)
- Append: `## [YYYY-MM-DD] ingest-meeting | <Client> — <meeting basename>` plus one
  line naming the pages touched. (Internal: `## [YYYY-MM-DD] ingest-meeting | internal — <basename>`.)

### 8 · Stamp `IngestedAt` — ALWAYS THE LAST WRITE
- `IngestedAt: YYYY-MM-DD HH:mm`. Because it is last, an interrupted run stays
  visibly un-ingested and is safely re-runnable.

## Idempotency (hard rule)
Every APPEND checks for its own line before writing. Re-runs must **not** duplicate
Timeline entries, Meeting Log lines, Tasks, or the live-call Work Session. The
session helper's source identity and `IngestedAt`-last make a re-run safe.

## Provenance (hard rule)
Every synthesized claim ends with a source link — ` ([[<meeting>]])`. A claim with
no source is a lint finding (G7).

## After running
Run `/lint` after a batch. Verify the meeting now shows `IngestedAt` and the dossier
`DossierUpdated` is ≥ the meeting's date.
