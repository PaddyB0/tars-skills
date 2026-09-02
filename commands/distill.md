---
description: Lift generalizable lessons from a client engagement up into the knowledge layer.
argument-hint: <client folder name>
---

# /distill <client>

The **up** step of the recursive-learning loop. Reads a finished or milestone-hit
engagement and promotes the *reusable* lesson into `Cowork/os/knowledge/` — scrubbed
of client-identifying detail — so the next engagement inherits it.

> Promoted to root `.claude/` under the one-OS-surface unification (Unified OS
> gameplan Phase 0). Runs from the vault root; all paths below are repo-root-relative.

Run at a natural endpoint: deliverable shipped, a thorny problem solved, a call
processed, or an engagement closed.

## Steps
1. **Read the engagement.** `Cowork/clients/<client>/MEMORY.md`, the relevant
   `outputs/`, and any notes. Identify what was *learned*, not just what was done.
2. **Separate general from specific.** For each candidate lesson ask: *would this
   help a different client in a similar situation?* If no, leave it in the client
   folder. If yes, it's a distillation candidate.
3. **Scrub.** Strip client name, account IDs, people, and figures. Keep the
   transferable mechanic (the procedure, the platform behavior, the pitfall).
4. **Place it.** Write or update the right page type in `Cowork/os/knowledge/`:
   - `runbooks/` — a repeatable procedure ("how to build a TB-based BvA with dynamic ranges").
   - `concepts/` — an FP&A method or Datarails platform mechanic.
   - `gotchas/` — a specific error and its fix.
   - `entities/` — durable knowledge about a system/data source (SAP, GP, QuickBooks, NetSuite, Spectrum).
   Cross-link with `[[page-name]]`; use the page frontmatter (`type, created, updated, tags, sources`).
5. **Discuss before finalizing.** Surface the proposed distillations to Patrick;
   one-line each. Don't bury a judgment call — confirm the general/specific split.
6. **Log it.** Update `Cowork/os/knowledge/index.md` and append to root `log.md`
   (`## [YYYY-MM-DD] distill | <client> → <pages touched>`).

## Rules
- Never copy raw client data into `Cowork/os/knowledge/`. Generalize or omit.
- On contradiction with an existing page: keep both, mark `> ⚠️ CONTRADICTION:`, surface to Patrick.
- Distillation is judgment work — prefer fewer, genuinely-reusable pages over many thin ones.
