---
description: End-of-session report-only protocol for staged Git-free separation; summarize local state without committing or publishing.
---

# /handoff

Run at the END of every working session. During staged Git-free separation this
command is report-only: it does not commit or push, and it does not infer authority
to create a handoff note or update PM state. Obsidian Sync is the vault file
transport; preserved repositories remain unchanged local evidence.

`python scripts/tars_state.py handoff` prints the mechanical draft of the
handoff note from this machine's runs; `--write` creates the `Handoffs/` note.
`/handoff` only reports unless the user separately asks to write.

## Steps
1. **Identify this machine.** Read `Cowork/.ai-os-machine` for the Executor label
   (uname fallback).
2. **Capture read-only state.** Report local HEAD, staged/unstaged/untracked counts,
   applicable evidence states, and whether a writer lease remains held. Do not
   change the index, refs, worktrees, or Sync configuration.
3. **Surface PM follow-through.** List any Work Session or Task updates that may be
   appropriate, but do not write them unless the user separately authorizes those
   schema-valid changes.
4. **Report the handoff in chat.** Summarize outcomes, validations, unresolved
   blockers, and the next safe action. Do not create a `Handoffs/` note unless the
   user separately requests it.
5. **Keep publication separate.** `/safe-push` is a distinct, explicitly authorized
   workflow. `/handoff` never invokes it and never implies commit or publication
   authority.

## Rules
- Do not pull, fetch, stage, commit, push, or mutate refs/worktrees.
- Evidence states are exactly `pass`, `fail`, `not_run`, and `waived`.
- A later publication or PM-write request requires separate authority and its own
  gates; this report does not grant it.
