---
name: review
description: Weekly PM rollup from the vault — overdue / due-this-week / in-progress tasks, hours by project & company (summed DurationMin), and stale in-progress tasks (>14d untouched). Output to chat; --note writes it to Notes/. Use when the user says "weekly review", "what's overdue", "how many hours on <client>", "status of my work".
---

# /review

Weekly rollup computed by reading task and work-session frontmatter directly
(never Base views — per `CLAUDE.md` hard rule 2).

## How to run

```bash
cd "<vault root>"
python .claude/skills/review/review.py            # uses today's real date
python .claude/skills/review/review.py --today 2026-07-02   # pin a date
```

The script prints a Markdown report. It computes:

- **Overdue** — `DueDate < today` and `Status != 🟢 COMPLETE`.
- **Due in 7 days** — `today ≤ DueDate ≤ today+7`, not complete.
- **In progress** — `Status == 🔵 IN PROGRESS`.
- **Stale in progress** — in-progress and `modified` older than 14 days.
- **Hours by project / by company** — from authoritative `Work Sessions/` on or
  after the official `2026-06-01` cutoff, grouped by `Project` / `Company`.
  Shows exact raw hours (`DurationMin / 60`) and Billable hours rounded upward per
  session to the next 30 minutes. Flagged import-duplicate rows are excluded.

## Output

- Default: print the report to chat, then add a one-line headline (biggest risk:
  most-overdue task, or the client with the most unbilled hours).
- `--note`: also write the report to `Notes/Weekly Review <YYYY-MM-DD>.md` with
  frontmatter `created`, `modified`, `tags: [review]`. Overwrite the same-day file
  if re-run; don't accumulate duplicates.

## Notes

- Exact `DurationMin` remains stored; rounding is reporting-only and applies only
  to `HoursType: Billable`.
- If a session has an unlinked `Project`/`Company`, it lands under
  `(unlinked)` — that's a signal to fix the session note, then re-run.
- This is read-only. It never writes to `Tasks/` or `Work Sessions/`.
