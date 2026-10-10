---
name: ingest-meeting
description: Source the meeting body from its Zoom transcript (Gong summary as fallback), ensure one authoritative live-call Work Session, then propagate a meeting into the wiki — fill Contacts, update the dossier, person pages, project Meeting Log, and strictly-gated Tasks, log it, then stamp IngestedAt last. This is the core Unified-OS loop. Use when the user says "ingest this meeting", "process the backlog", or after /meeting files a note. Default target = every Meetings/ note with empty IngestedAt, oldest first.
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
- **Interview** (`Meetings/Datarails - Interview *.md`) → the note is gitignored because it
  holds a hiring assessment. Every write outside that note (Tasks, Work Session,
  `log.md`) names the candidate and links the note, and carries **no assessment
  content**: no strengths, weaknesses, fit, or recommendation.

## Steps (in order — the stamp is always last)

### 0 · Source the body: Zoom transcript first, Gong as fallback

The importer (`Cowork/os/automations/gong-sync`) creates the note with identity,
timing, `GongId`, `CallUrl`, `GongDurationMin`, and Gong's own Key Points and Next
Steps. This step replaces that body with one written from the Zoom transcript
when a clean transcript exists. Run it only while `IngestedAt` is empty.

**0a · Already sourced.** If `ZoomMeetingUUID` is set, the body was already
written from that transcript. Do not fetch or rewrite. Go to step 1.

**0b · Find the recording.** Call the Zoom connector's `recordings_list` with
`from` = the `StartTime` date and `to` = the next day. If the result was saved to
a file, pass that path. If it came back inline, do not retype it: Write one slim
row per recording to a scratchpad file as a JSON list of
`{"uuid", "id", "topic", "start", "end", "transcript"}` (format in the script
docstring). Connector output and its slim copies never go in the vault: the
recording list carries playback passcodes and share URLs. Then, from the vault
root:

```bash
python3 .claude/skills/ingest-meeting/zoom_transcript.py match \
  --meeting "Meetings/<meeting filename>.md" --recordings "<json path>"
```

The script requires the Zoom topic to equal `GongTitle` (or the `CallUrl` meeting
number), one completed transcript of at least 3 minutes, and coverage of at least
half the call. Its docstring is the contract.

- `match` → 0c.
- `fallback` (`no-timing`, `no-identity`, `no-recording`, `split-recording`,
  `partial-recording`) → 0d. Never pick a recording by hand.
- Connector unavailable or erroring → 0d with reason `zoom-unavailable`.

**0c · Write the body from the transcript.**
1. Call `get_recording_resource` with `meetingId` = the matched `uuid` and
   `types` = `transcript`. If the result was saved to a file, pass that path. If
   it came back inline with one clip, Write a scratchpad text file with one line
   per timeline entry, `[HH:MM:SS] <display_name>: <text>`, and drop every other
   field. An inline result with more than one clip goes to 0d with reason
   `split-recording`. Then:
   ```bash
   python3 .claude/skills/ingest-meeting/zoom_transcript.py render \
     --meeting "Meetings/<meeting filename>.md" --resource "<path>" --uuid "<uuid>"
   ```
   This writes `Transcripts/<meeting basename>.md`, which is gitignored. Never
   copy transcript text into any tracked file.
2. Read the whole transcript file, then write the three sections:
   - `## Recap` — 2–4 sentences: why the call happened, what was decided, what
     changed.
   - `## Key Points` — 5–10 bullets, most important first, as
     `- <Topic>: <what was said or decided>`. Keep the specifics (numbers,
     systems, tables, names). A long call may group bullets under `###`
     subheadings. An interview keeps the interview layout:
     `### Key Takeaways` with `#### Strong Points`, `#### Weak Points` and
     `#### Why Datarails`.
   - `## Next Steps` — `- [ ] <Owner> will <action>` for commitments actually
     made on the call, with a date only when one was stated. The owner is
     "Patrick" or the person's full CRM name.
   Use only what the transcript says. Zoom's speech recognition mangles names
   and products ("Cloud" for Claude, misspelled people); correct them only when
   context makes the fix certain.
3. Re-read the note. If it changed since you read it, stop. Otherwise replace
   the body and set `ZoomMeetingUUID: "<uuid>"` in one write. Leave every other
   frontmatter key alone.

**0d · Fallback: keep the existing body.** The body stays as written, by the
importer or by hand. It must contain substantive content in at least one of
`## Recap`, `## Key Points`, or `## Next Steps` beyond the importer scaffold and
any calendar-review marker. If all three are empty or placeholders, **STOP**
before the Work Session, propagation, task, log, or `IngestedAt` writes.
Ingestion must never turn an empty receipt into authoritative wiki state. The
stop reason depends on whether Gong owns the note:
- `GongId` present → `gong-pending`: Gong's summary has not arrived yet and a
  later importer run may fill it.
- No `GongId` → `no-source`: no Zoom transcript and no Gong recording, so nothing
  will fill the body on its own. Patrick must add notes or a transcript.

Only the importer's one-time placeholder transition (see the gong-sync README)
and 0c may write a Meeting body. After `IngestedAt` is set the body is immutable.

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
  Never use `CallType`, `Other`, or a synthetic company; the enum itself is
  owned by `/vault-schema`.
- **Do not touch the meeting body** outside step 0c.

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

### 6 · Tasks — review, then layer or create
Every **Patrick-owned, actionable** Next Step is matched against existing Tasks
before anything is written. A new Task is the last resort, not the default.

**6a · Build the candidate set.** Read the frontmatter and body of every Task
whose `Project` is the meeting's Project, plus every Task with the same `Company`
on another Project. Include open Tasks (any `Status` except `🟢 COMPLETE` and
`⚫ CANCELED`) and Tasks completed in the last 30 days. Read `Description` and
`### Progress Notes`, not just the filename.

**6b · Match on the outcome.** A hit is a Task that delivers the same outcome
(same deliverable, fix, or decision), even when the wording, filename, or scope
differs. Also merge Next Steps within the same meeting that describe one outcome
into a single action item before matching.

**6c · Act on the result.**
- **Open-Task hit → layer, never duplicate.**
  - Prepend one Progress Notes line (newest first) that states what the call added,
    not just that it came up: `- YYYY-MM-DD — <new context: scope, decision,
    dependency, blocker, owner or date> ([[<meeting>]])`. If the call added nothing
    new, write `- YYYY-MM-DD — re-confirmed in [[<meeting>]]`.
  - If the call changes what "done" means, append one sourced sentence to
    `Description`. Never rewrite or delete existing Description text.
  - Fill an empty `DueDate` or raise `Priority` only when the meeting states it.
    If the meeting contradicts a value already set, keep the existing value and
    record the conflict in the Progress Notes line with a `⚠️` prefix.
  - Add a `BlockedBy` link only when the call names a blocking Task that exists.
  - Never change `Status`. Update `modified`.
- **Completed-Task hit** → do not reopen it. A follow-up Task is a new Task: it
  must pass the 6d gate, and its `Description` names the prior Task as a wikilink.
- **Ambiguous** (two plausible Tasks, or partial overlap) → write nothing for that
  item. List it in the run report with the candidate Tasks for Patrick to decide.
  It does not block the stamp.
- **Miss** → apply the 6d gate.
- **Client-owed steps → dossier checklist (step 3), never Tasks.**

**6d · New-Task gate (strict).** Task overload is the failure this gate exists to
prevent. A new Task is created only when the item passes **all five** tests:
1. The call explicitly assigned it to Patrick. No inferred owner.
2. It has a concrete deliverable with a verifiable done state. "Build out more
   reports over the next few weeks" fails; "Send the controller the eliminations
   template" passes.
3. It was not finished during the call.
4. It is not scheduling or logistics (move a meeting, send an invite, attend).
5. No open Task covers it (6b).

At most **2** new Tasks per meeting. When more pass, keep the 2 with the clearest
deliverable and nearest stated date. Items that fail the gate or exceed the cap
create no Task. For a client meeting they still reach the dossier's "We owe them"
checklist in step 3. Every one is listed in the run report as a `candidate` with
the test it failed or `cap`, so Patrick can promote it with `/task`.

To create: load `vault-schema` for the task enums, then follow the `/task`
contract: `Status: ⚪ TO DO`, `Project`, `Company`, `Description` **ending with
the source link**. Dates/priority only if stated in the meeting, **never
invented**. An interview Task names the candidate and links the note, with no
assessment content.

**6e · Report.** The run report lists each action item as `created`, `layered`
(with the Task link), `ambiguous`, or `candidate` (with the reason).

### 7 · OS log (`log.md` at vault root)
- Append: `## [YYYY-MM-DD] ingest-meeting | <Client> — <meeting basename>` plus one
  line naming the pages touched. (Internal: `## [YYYY-MM-DD] ingest-meeting | internal — <basename>`.)

### 8 · Stamp `IngestedAt` — ALWAYS THE LAST WRITE
- `IngestedAt: YYYY-MM-DD HH:mm`. Because it is last, an interrupted run stays
  visibly un-ingested and is safely re-runnable.

## Idempotency (hard rule)
Every APPEND checks for its own line before writing. Re-runs must **not** duplicate
Timeline entries, Meeting Log lines, Tasks, Task Progress Notes lines (a line
already linking this meeting counts), or the live-call Work Session. The
session helper's source identity and `IngestedAt`-last make a re-run safe.
`ZoomMeetingUUID` marks a body already written from the transcript, so a re-run
never fetches or rewrites it; `render` rewrites the transcript file only when its
content differs.

## Provenance (hard rule)
Every synthesized claim ends with a source link — ` ([[<meeting>]])`. A claim with
no source is a lint finding (G7).

## After running
Run `/lint` after a batch. Verify the meeting now shows `IngestedAt` and the dossier
`DossierUpdated` is ≥ the meeting's date. The run report states each meeting's
body source: `zoom` or `gong (<fallback reason>)`.
