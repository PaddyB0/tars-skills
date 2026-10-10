---
description: Unattended nightly /ingest-meeting over the IngestedAt backlog — full propagation, per-meeting stop on exceptions, lint, report in chat only.
---

# /night-ingest

Run `/ingest-meeting` unattended over every meeting awaiting ingestion, then lint
and return one concise morning report. This is the only nightly routine that writes
vault content. Owner decision 2026-09-24: full ingest, including new Contact pages
and new Tasks, runs unsupervised.

## Boundary

Allowed writes are exactly the pages `/ingest-meeting` owns: meeting frontmatter,
the Meeting body through the skill's step 0c only, `Transcripts/` through
`zoom_transcript.py render`, `CRM/Contacts/` (new and existing person pages),
`CRM/Clients/` dossiers, Project `## Meeting Log`, `Tasks/`, the live-call Work
Session via `ensure_session.py`, root `log.md`, and the `/lint` log line. Nothing
else.

- Root CLAUDE.md hard rules 1 and 3 apply in full (protected paths and the plugin data file; Git is never a transport and never mutated).
- Never fill a Gong placeholder.
- Do not run `/lint --fix`, `/pulse`, `/handoff`, `/safe-push`,
  `/submit-timesheets`, or any other workflow.
- Obsidian-git auto-commits on its own schedule.
- The only connector allowed is Zoom, read-only: `recordings_list` and
  `get_recording_resource`, as step 0 of the skill directs. No other connector or
  external API.
- If access, a command, or a permission is unavailable, stop that meeting, record
  it as an exception, and continue. Do not seek broader access.

## 1. Establish the run

1. Read root `CLAUDE.md` and the `ingest-meeting` skill in full. The skill is
   authoritative for every step and hard rule. Do not work from a summary.
2. Use the real local date in `America/Edmonton` as `TODAY`.
3. Record `git branch --show-current`, `git rev-parse --short=12 HEAD`, and
   `git status --short | wc -l`. A dirty worktree is normal and not a blocker.
4. Build the queue:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
  python3 Cowork/os/automations/ingest-backlog.py --today <TODAY>
```

   The queue is every listed meeting, oldest `StartTime` first, then undated ones.
   Process at most **12** per run. The rest roll to the next night and are listed
   in the report.

## 2. Ingest, one meeting at a time

For each queued meeting:

1. Re-read the note. If it now has `IngestedAt`, skip it as done elsewhere.
2. If any file the run will touch has a sibling conflict copy (a name containing
   `conflict` or `(1)`), or a file changed between your read and your write, stop
   that meeting before further writes.
3. Invoke the `ingest-meeting` skill with the meeting's filename as its argument
   and follow it end to end, including step 0 (Zoom transcript, Gong fallback)
   and step 2 (`ensure_session.py`). Save connector JSON to the scratchpad, never
   to the vault.
4. A skill STOP is a normal outcome, not a failure. Record the meeting and the
   exact reason, leave it un-stamped, and move to the next meeting.

Judgement calls the skill leaves to you apply unattended with these rules:

- New Contact page only for an attendee named in the body with a full name and a
  resolvable Company. Anyone else stays plain text "(no page yet)".
- New Task only through the skill's 6d gate: all five tests, at most 2 per
  meeting. No inferred owner, date, or priority.
- When dedupe against open tasks is uncertain, append a Progress Notes line to the
  closest match rather than creating a near-duplicate, and list it in the report.

## 3. Lint

After the last meeting, run the `lint` skill without `--fix`. Its `log.md` line is
allowed. Any new error on a page this run touched is a RED finding. Do not repair
it.

## 4. Return the report

Return the report in chat only. Do not file it anywhere.

```markdown
# TARS Night Ingest — YYYY-MM-DD

**Verdict:** GREEN | YELLOW | RED
**Observed:** <branch> @ <12-char SHA> · <n> dirty paths at start
**Ingested:** <n> of <queue size> · **Stopped:** <n> · **Rolled over:** <n>

## Ingested
- <meeting> — source zoom | gong (<fallback reason>) — <pages touched: dossier, n people, meeting log, n tasks new/carried, session CREATED/REUSED>

## Created for review
- Contacts: <new person pages>
- Tasks: <new tasks, with project>
- Task candidates: <action items held back by the 6d gate, with the failed test or `cap`>
- Uncertain dedupe: <task that received a carried line instead of a new task>

## Stopped
- <meeting> — <exact reason: gong-pending, no-source, ensure_session exception text, conflict copy, permission>

## Lint
- <errors/warnings; any finding on a page this run touched>
```

Verdict rules:

- **RED** — a lint error on a touched page, a conflict copy, or a write outside the
  boundary.
- **YELLOW** — any stopped meeting other than `gong-pending` (a `no-source` stop
  never resolves on its own), any rollover, any uncertain dedupe, or any
  `zoom-unavailable` fallback.
- **GREEN** — every queued meeting ingested or `gong-pending`, and lint clean on
  touched pages.
