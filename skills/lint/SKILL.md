---
name: lint
description: Unified vault lint — four passes (schema S1–S4 · propagation P1–P8 · graph G1–G7 · agent surface AS1–AS7) over every TARS note and the wiki layer. Run after any batch of writes and before every handoff. Use --fix for mechanical fixes only. Use when the user says "lint the vault", "run lint", "check the vault".
---

# /lint [--fix]

One lint, three passes. Full contract: [[TARS Unified OS - Schema]] § 6. A note with a wrong
enum, malformed key, or empty-string date silently disappears from every Base view —
this catches that, plus propagation gaps (un-ingested meetings, stale dossiers,
renewal orphans) and graph health (broken links, orphans, provenance).

## How to run

```bash
cd "<vault root>"
PYTHONIOENCODING=utf-8 python .claude/skills/lint/lint.py
```

- Exit `0` = no errors (warnings never fail the run). `--fix` = **mechanical** fixes
  only (empty-string dates → omitted). `--today YYYY-MM-DD` overrides "now" for the
  age-based propagation checks.
- `PYTHONIOENCODING=utf-8` is **required on Windows** — the console defaults to
  cp1252 and crashes on the emoji enum values.
- The script's schema constants are re-derived from `Administrator/FileClasses/*.md`
  — **that folder is the source of truth.** If a fileClass changes, update `lint.py`'s
  `DATE_FIELDS` / `NAME_RE`; `ENUMS` is derived from `schema.json`.

## Pass 1 — Schema (S1–S4, scripted)
Frontmatter present/parseable · `fileClass` correct for the folder · no duplicate/
malformed keys · enums exact (emoji/case/spacing) · dates parse, never `""`,
date-only fields reject a time · wikilink fields resolve · filename conventions
(warning). Plus the Cowork↔vault **bridge** checks (`cowork_client` resolves, one
company note per folder, bidirectional CLAUDE.md pointers).

Phase 2 scheduling checks keep legacy Tasks valid while enforcing opted-in Task
ownership/readiness, active Habit cadence/time/policy requirements, and flat
Scheduling Policy windows, capacity, buffer, horizon, and target-calendar rules.
`Habits/` and `Scheduling Policies/` are mapped folders and are linted like every
other FileClass. Optional Phase 4 energy and normal-hours preferences must be
non-empty scalar same-day `HH:mm-HH:mm` windows when present.

## Pass 2 — Propagation (P1–P8)
Scripted in `lint.py`: physical Work Session fields and enums (`Task`, `Project`,
`ActivityType`, `Audience`, `StartTime`, `EndTime`) with legacy keys rejected ·
post-cutoff Meetings missing `EndTime` surfaced as duration-ledger exceptions ·
**P1** post-cutover un-ingested meeting > 2 days old · **P2**
`DossierUpdated` behind the client's latest ingested meeting · **P5** client-folder
commit with no same-day Work Session · **P6** ingested meeting with an empty body
(capture failure that looks "done") · **P7** active client beyond its configured
meeting cadence (policy in `freshness-policy.json`; `null` means on-demand) ·
**P8** open task pointing at a `🟢 complete` engagement while
the company has an active one (renewal orphan — `--fix`-able re-point).

Reader-driven (judgment; act on these after reading the script output):
- **P3** — unchecked dossier commitment > 30 days old → surface it, don't auto-close.
- **P4** — meeting `Contacts: []` while the body names attendees → fill + create pages
  (this is what `/ingest-meeting` does; `--fix` intent, run the ingest).

## Pass 3 — Graph (G1–G7)
Scripted: **G3** orphan pages in `Notes/` + `Cowork/os/knowledge/` (no inbound links) ·
frontmatter-link resolution (part of S) · bridge join-key direction (G5, via bridge).

Reader-driven (judgment):
- **G1** body wikilinks that don't resolve (beyond frontmatter).
- **G2** person referenced (People / `Contacts`) with no CRM note — plain-text
  "(no page yet)" mentions are **compliant**; offer to create real ones.
- **G4** dossier claim contradicting a client `MEMORY.md` → **flag for human, never
  auto-fix**.
- **G6** dossier `## People` ≠ frontmatter `ContactName` (mirror drift) → reconcile.
- **G7** synthesized claim with no source link (provenance rule) → add the source.

## Pass 4 — Agent surface (AS1–AS7, scripted)
`python scripts/agent_surface_lint.py` checks settings JSON, hook wiring, skill and
command frontmatter, the always-loaded word ceiling, and **AS7** schema drift: the
`/vault-schema` field tables, `Administrator/FileClasses/`, and `lint.py` `ENUMS` (derived from `schema.json`)
must agree (it runs `python scripts/build_vault_schema.py --check`). The check
contract lives in that script's `--help`.

## --fix scope (mechanical only)
Empty-string dates → omitted (scripted). P8 renewal re-point and P4 contact-fill are
**intent**-fixable but run through `/ingest-meeting` / a deliberate edit, never a
blind rewrite. Never let `--fix` touch enum/wikilink/judgment issues.

## After running
- Report errors first, then warnings — don't hide warnings.
- Append a dated entry to `Notes/Vault Lint Log.md` (create if missing):
  `## YYYY-MM-DD HH:mm — N notes, E errors, W warnings` + a one-line summary and any
  fixes applied. Append a `## [YYYY-MM-DD] lint | summary` line to root `log.md`.
- Known-acceptable warnings: `TAM Team Weekly Meeting` (recurring internal note, no
  dated instance); plain-text "(no page yet)" people (G2, by design).

## Watch-outs
- `crm_contacts` (plural) is the correct fileClass; the stock template ships
  `crm_contact` (singular) — always an error, fix to plural.
- Obsidian Sync and human edits may change notes during lint. Re-read before any
  fix, never clobber concurrent work, and stop on a conflict-copy error.
