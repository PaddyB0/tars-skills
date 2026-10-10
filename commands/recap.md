---
description: Client call recap — for recent external Gong calls, mint a customer share link, write the recap, leave a Gmail draft, digest in chat.
---

# /recap

For each recent external Gong call, write a client-facing recap with a link to
the recording and leave it as a Gmail draft. **Draft-only: never send, never
reply on a thread, never edit a Meeting or CRM note.**

Config lives in `Cowork/os/automations/recap-followup/rules.md`. Read it first,
every run. It owns share-link settings, recipients, scrub, subject, body shape,
and the Gmail label. This file owns only the procedure.

## Steps

1. **Load config.** Read `rules.md`, `~/.claude/VOICE.md`.
2. **Select.** From the repo root:
   `python Cowork/os/automations/recap-followup/select_candidates.py --vault .`
   An argument like `/recap 7d` maps to `--days 7`. `/recap <GongId>` maps to
   `--gong-id <GongId>`. Exit 2 means a bad vault path: stop. Exit 1 means a
   corrupt `state.json`: stop and report, never treat it as empty.
3. **Per candidate, oldest first.**
   1. Read the client folder's `CLAUDE.md` (`Cowork/clients/<Company>/`) when it
      exists.
   2. **Share link** (Claude in Chrome). Open `call_url`. Install the clipboard
      hook with `javascript_tool`: patch `navigator.clipboard.writeText`,
      `navigator.clipboard.write` and `document.execCommand('copy')` to push the
      copied text into `window.__copied`. Click Share call (top right), then
      Share with customers, then the Get link tab. Check the settings against
      `rules.md` and fix any that differ. Click Copy link, then read
      `window.__copied`. Accept only a `https://` Gong URL. On any failure or
      permission denial, use the placeholder `[Gong share link]`.
   3. **Write.** Subject and body per `rules.md`, from `client_key_points` and
      `client_next_steps` only. Re-read the draft against the scrub: no amount,
      price, funding, or internal Datarails item may survive. Then run an
      unslop pass and strip any em or en dash.
   4. **Draft.** Gmail `create_draft` to the candidate's `contacts` emails.
      Apply label `Label_28` to the draft's message.
   5. **Record.** `python Cowork/os/automations/recap-followup/record_draft.py
      --gong-id <id> --meeting "<meeting>" --share-url "<url or placeholder>"
      --draft-id <draft id>`.
4. **Digest, in chat only.** One line per draft: company, recipients, link
   minted or placeholder. Then `skipped` entries with reasons, and any
   `unresolved_contacts` by name. Flag that every draft needs Patrick's review
   before sending, and that a placeholder draft needs the link pasted in.

## Rules

- Mutations allowed: Gong share settings on the call being recapped,
  `create_draft`, the `Label_28` label on that draft, and `state.json` through
  `record_draft.py`. Nothing else.
- Never `send_message`, `reply`, or `update_draft` to send.
- Never address an `@datarails.com` contact. Never guess an email for an
  unresolved contact.
- A GongId already in the ledger is never drafted again. `record_draft.py
  --force` only on Patrick's request.
