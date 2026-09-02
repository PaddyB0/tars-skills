---
description: Email triage — classify + label new inbox threads, draft client-external replies, digest in chat.
---

# /triage

Triage Patrick's inbox: label new threads into the `[Superhuman]/AI/*` taxonomy,
create reply drafts for client-external threads that need one, and report a
digest in chat. **Label-only: never send, never archive, never trash, never
change read state.**

Config lives in `os/automations/email-triage/rules.md` — read it first, every
run. It owns the label IDs, sender rules, client map, and drafting rules; this
file owns only the procedure.

## Steps

1. **Load config + state.** Read `rules.md` and `state.json` (same folder).
   Window = `state.last_run` → now; no state file → last 48h. An argument like
   `/triage 7d` overrides the window.
2. **Fetch.** `search_threads` with `in:inbox after:<window>` (paginate to
   completion). Also fetch `in:inbox is:unread` older than the window on a
   `catchup` argument. Skip threads already carrying a Gong label, and skip
   any bucket-label already applied to the thread (idempotent re-runs).
3. **Classify each thread.**
   - Sender rules from `rules.md` first — exact sender, then domain, then
     subject-prefix rules.
   - Everything else by judgment: Respond / Waiting / Meeting / FYI / News /
     Pitch / Marketing / System per the taxonomy table. When the snippet is not
     enough to call it, `get_thread` and read the latest message.
   - A thread where Patrick sent the last message and is awaiting the other
     side → Waiting.
4. **Label.** `label_thread` with the bucket's label ID. One bucket label per
   thread (plus Drafted where step 5 applies). Never remove labels a human set.
5. **Draft** (client-external Respond threads only, per the drafting rules in
   `rules.md`). Read `~/VOICE.md` + the mapped client folder's `CLAUDE.md` /
   `MEMORY.md`, `get_thread` for full context, then `create_draft` as a reply
   on the thread. Label the thread Drafted. Skip (with a digest note) rather
   than fabricate specifics.
6. **Digest — in chat only.** Lead with what needs Patrick:
   - **Respond** — one line each: who / what they need / draft ready or why not.
   - **Meeting changes** — declines and reschedules called out loudly; plain
     accepts as a count.
   - **Waiting** — threads where Patrick is owed a reply, oldest first.
   - **Everything else** — counts by bucket, not lists (expand News/Pitch on request).
7. **Save state.** Write `state.json` with the new `last_run`. If a new sender
   or domain appeared that the rules should cover, append it to `rules.md`
   (sender rules or client map) and say so in the digest.

## Rules

- Mutations allowed: `label_thread`, `create_draft`, `state.json`, `rules.md`
  additions. Nothing else — no send, no archive, no trash, no spam-marking,
  no read-state changes, no label deletion.
- Internal `@datarails.com` threads are never drafted.
- Gong notifications belong to the gong-notion Apps Script — hands off.
- Drafts are proposals: flag in the digest that every draft needs Patrick's
  review before sending.
