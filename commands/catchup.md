---
description: Start-of-session protocol — verify Sync and local preservation state, read the vault task picture, and brief Patrick without Git mutation.
---

# /catchup

Run at the START of every working session, before any changes. TARS and Cowork share
one OS surface, while Obsidian Sync is the vault file transport and preserved Git
repositories remain local evidence during staged separation. Run from the vault
root; all paths below are vault-root-relative.

## Steps
1. **Identify this machine.** Read `Cowork/.ai-os-machine` for the Executor label
   (`Code-Mac`, `Code-Win`, `Code-Work`). If absent, fall back to `uname`.
2. **Confirm Sync health.** Obtain a fresh human-observed Obsidian Sync state. It
   must say `Fully synced` with zero errors before mutation; otherwise report
   `not_run` or `fail` and stay read-only. Never substitute a Git network command.
3. **Verify local preservation state.** Read local HEAD and status without changing
   refs, the index, or worktrees. Read the newest `Handoffs/HO *.md` by filename.
   Its `sha` records the content commit immediately before the handoff note.
   Verify that SHA exists and is an ancestor of local HEAD with
   `git merge-base --is-ancestor <sha> HEAD`. Report both the content SHA and
   current HEAD. Handoffs dated before 2026-07-24 are legacy artifacts from
   before the clean-history rewrite; report a missing legacy SHA but do not
   block. For a handoff dated 2026-07-24 or later, a missing or non-ancestor SHA
   is a hard mismatch: STOP and surface it.
4. **Read the TARS vault** (repo root — always present now; no `.tars-vault`
   check). By frontmatter, not Bases:
   - **Overdue** — `Tasks/` with `DueDate < today` and `Status != 🟢 COMPLETE`.
   - **Due in 7 days** and **🔵 IN PROGRESS** tasks.
   - Helper: `PYTHONIOENCODING=utf-8 python .claude/skills/review/review.py --today <YYYY-MM-DD>`
     produces exactly this rollup.
5. **Meeting ingest backlog check (core loop trigger).** Meetings arrive
   automatically (Gong → vault), so nothing else reliably triggers ingest — this
   check is how the backlog stays at zero. List every `Meetings/*.md` whose
   `IngestedAt` is empty (grep the frontmatter key). Flag any older than 2 days as
   overdue (lint P1). Surface the count; offer to run `/ingest-meeting` (which
   defaults to the whole backlog, oldest first).
6. **Brief Patrick.** One concise digest: Sync state, local HEAD, last repo handoff,
   the vault task picture, ingest backlog, and any discrepancies. Wait for direction
   before changing anything.

## Rules
- Read-only until Patrick directs the work.
- Do not pull, fetch, stage, commit, push, or mutate Git refs/worktrees.
- Keep technical knowledge git-native under `Cowork/os/`; the vault wiki points
  to it rather than copying it (see `Cowork/CLAUDE.md` § Boundaries).
