---
description: Read-only dawn control-tower brief — rank today's work, client risk, meeting backlog, and overnight exceptions without changing TARS.
---

# /morning-brief

Produce a concise, evidence-backed start-of-day brief from the current local TARS
state. This is an independent routine: it may use a Night Watch report if one is
present in the conversation, but it must still verify time-sensitive PM facts
itself.

## Non-negotiable boundary

This routine is read-only:

- Root CLAUDE.md hard rules 1 and 3 apply in full (protected paths and the plugin data file; Git is never a transport and never mutated).
- Do not edit PM state, dossiers, meetings, work sessions, project notes, or
  automation artifacts.
- Do not create a prep note, weekly-review note, pulse, audit, log entry, task,
  work session, or handoff.
- Do not use `/lint --fix`, `/ingest-meeting`, `/pulse`, `/handoff`,
  `/submit-timesheets`, or an external write-capable connector.
- Missing or stale data must remain visible as a gap. Do not open raw meetings to
  manufacture certainty that the dossier does not support.
- If a read-only check cannot run, mark it **UNVERIFIED** and continue. Do not
  broaden permissions during an unattended run.

## 1. Establish today's local state

1. Read root `CLAUDE.md`.
2. Use the real local date in `America/Edmonton`; call it `TODAY`.
3. Record the current branch, HEAD, and `git status --short`. Do not pull, fetch,
   switch branches, or clean the worktree.
4. If a Night Watch report is available in the conversation, treat it as a lead,
   not as current truth. Note its observation date and SHA.

## 2. Refresh the time-sensitive evidence

Run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
  python3 .claude/skills/review/review.py --today <TODAY>

PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
  python3 Cowork/os/automations/ingest-backlog.py \
  --vault /path/to/TARS --today <TODAY>

PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 \
  python3 Cowork/os/automations/verify_automation_health.py \
  --runtime-vault /path/to/TARS
```

Non-zero exit from the backlog checker means overdue meetings exist; it is a
finding, not a failed routine.

## 3. Build the control-tower view

Read frontmatter directly, never Base views.

1. **Today:** open tasks due or overdue, ranked by Critical/High first, then due
   date. Keep existing `🔵 IN PROGRESS` work visible.
2. **This week:** the smallest set of due-in-seven-days tasks that could become
   tomorrow's problem.
3. **Portfolio risk:** inspect active/at-risk project notes and their linked CRM
   dossiers. Return at most three client risks, supported by dossier sources.
   If `DossierUpdated` is stale or absent, say so rather than inventing status.
4. **Meeting propagation:** show backlog count, overdue count, oldest meeting,
   and the exact supervised `/ingest-meeting` queue to consider.
5. **Hours and billing:** surface unlinked sessions, reporting exceptions, and
   the largest raw-versus-rounded billable-hours concern from `/review`. Never
   stage or submit a timesheet.
6. **Overnight exceptions:** carry forward only Night Watch findings that still
   reproduce or are explicitly labeled historical/unverified.

Every synthesized client claim must end with a dossier wikilink. Keep client-owed
commitments in the dossier; do not reinterpret them as Patrick-owned tasks.

## 4. Make a proposed day plan

Propose, but do not execute:

- **First move:** one concrete action that reduces the greatest near-term risk.
- **Deep-work block:** one bounded outcome, preferably an existing in-progress or
  high-priority task.
- **Admin block:** meeting ingestion, task hygiene, or time/billing review that
  requires Patrick's approval.
- **Can wait:** one tempting but lower-value item to defer.

Do not assign new dates, change priority, close commitments, or infer approval.

## 5. Return the brief

Return in chat only; do not write a note.

```markdown
# TARS Morning Brief — YYYY-MM-DD

**Start here:** <one concrete first move>
**System confidence:** HIGH | MEDIUM | LOW — <why>

## Today
1. <task · priority · due/status · why now>

## This week
- <only material upcoming pressure>

## Portfolio watch
- **Client** — <state · risk · next decision> ([[Client]])

## Propagation and billing
- Meetings: <backlog/overdue/oldest and proposed supervised queue>
- Hours: <material exception or "no material exception">

## Overnight/system exceptions
- <reproduced, historical, or unverified finding>

## Proposed day shape
- First move: ...
- Deep work: ...
- Admin: ...
- Can wait: ...

## Decisions for Patrick
- <decision; omit section if none>
```

Aim for a brief that can be read in two minutes. If there is nothing urgent, say
so plainly and recommend protecting the deep-work block.
