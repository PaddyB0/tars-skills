---
name: prep
description: Read-only call brief for a client, synthesized from the CRM dossier alone. Sections - snapshot, since last call, we owe / they owe, open tasks, watch-outs, suggested agenda. Use when the user says "prep me for the <client> call", "brief me on <client>", "/prep <client>". Add --file to write it to Notes/.
---

# /prep <client> [--file]

Produce a call brief for `<client>` **from the dossier alone**. This is the payoff
of the propagation loop: if `/prep` can't produce a correct brief without opening a
single meeting note, the loop isn't propagating enough. Spec: [[TARS Unified OS - Schema]] § 5.

## Read (in this order)
1. `CRM/Clients/<client>.md` — the dossier body (Snapshot, People, Commitments,
   Timeline, Pointers).
2. Open tasks — grep `Tasks/*.md` for `Company: "[[<client>]]"` (or the client's
   project) with `Status != 🟢 COMPLETE`.
3. Person pages for the expected attendees (`CRM/Contacts/`).
4. The last 1–2 dossier Timeline entries for recency — **not the raw meetings**.
   (If the dossier is thin, say so and name what's missing — do not silently open
   meeting notes to paper over a propagation gap.)

## Output — the brief (chat by default)
Every claim carries its dossier source link.

- **Snapshot** — where the engagement stands, current risk (from `## Snapshot`).
- **Since last call** — the newest 2–4 Timeline lines.
- **We owe them / They owe us** — the two `## Commitments & open loops` checklists,
  unchecked items only.
- **Open tasks** — Patrick-owned, by priority/due.
- **Watch-outs** — renewal deadlines, contradictions (⚠️ lines), stale loops.
- **Suggested agenda** — 3–5 bullets derived from the above.

## Rules
- **Read-only.** `/prep` never writes to the dossier, tasks, or meetings.
- `--file` → write the brief to `Notes/Prep - <Client> YYYY-MM-DD.md` with a
  `## Sources` section of the dossier/contact wikilinks used (file-back convention).
- If a needed fact isn't in the dossier, name the gap — that's a signal to ingest,
  not a reason to break read-only.
