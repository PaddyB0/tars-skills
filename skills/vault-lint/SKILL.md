---
name: vault-lint
description: Validate every TARS note against the live fileClasses — required keys, exact enum values, parseable dates, resolving wikilinks, filename conventions. Run after any batch of writes and before every handoff. Use --fix for mechanical fixes only.
---

# /vault-lint

Validate the whole vault against the fileClass schema. This is the TARS twin of
Cowork's `/lint`. A note with a wrong enum, malformed key, or empty-string date
silently disappears from every Base view — this catches that before the human does.

## How to run

```bash
cd "<vault root>"
PYTHONIOENCODING=utf-8 python .claude/skills/vault-lint/lint.py
```

- Exit code `0` = clean (no errors). Warnings do not fail the run.
- Add `--fix` to apply **mechanical** fixes only (empty-string dates → omitted).
  Never let `--fix` touch enum/wikilink/judgment issues — fix those by hand.
- `PYTHONIOENCODING=utf-8` is required on Windows: the console defaults to cp1252
  and crashes on the emoji enum values otherwise.

## What it checks (per note, per fileClass)

The schema constants in `lint.py` are re-derived from
`Administrator/FileClasses/*.md` — **that folder is the source of truth.** If a
fileClass changes, update `lint.py`'s `ENUMS` / `DATE_FIELDS` / `NAME_RE` to match.

1. Frontmatter present and parseable; `fileClass` correct for the folder.
2. No duplicate or malformed frontmatter keys (e.g. `"HoursType:":`).
3. Enum fields hold **exact** allowed values (emoji, case, spacing) — including
   list-valued Select fields like meeting `CallType`.
4. Date fields parse as `YYYY-MM-DD` or `YYYY-MM-DD HH:mm`; never `""`.
   Date-only fields (`created`) reject a time component. Work Sessions use
   `StartTime`/`EndTime`; legacy session keys are errors after physical migration.
5. Wikilink fields resolve to a real note basename in the vault.
6. Filename matches the fileClass naming convention (warning only):
   - session → `<Client> - WS YYYY-MM-DD HHmm`
   - meeting → `<Client> - <Kind> (YYYY-MM-DD)`

### Bridge checks (Cowork ↔ vault)

Run only when `Cowork/clients/` exists (skipped in a vault-only checkout). They
enforce the **client ≠ engagement** identity model (see the root `CLAUDE.md` §
Cowork bridge):

7. Every `cowork_client:` on a project/company note resolves to a real
   `Cowork/clients/<folder>/` directory.
8. Every client folder (except `_template`) has **exactly one** CRM company note
   pointing at it via `cowork_client:` — zero is an error, more than one is an error.
9. Each client `CLAUDE.md` carries resolvable **bidirectional** pointers —
   `**TARS project:**` and `**TARS company:**` — and each target resolves to a real
   note (missing pointer = warning; dangling target = error).

## After running

- Report the result as-is (errors first, then warnings). Don't hide warnings.
- Append a dated entry to `Notes/Vault Lint Log.md` (create it if missing):
  `## YYYY-MM-DD HH:mm — N notes, E errors, W warnings` plus a one-line summary
  and the fixes applied. Keep it terse; it's an audit trail, not prose.
- Known acceptable warning: `TAM Team Weekly Meeting` (a recurring internal
  meeting note with no dated instance) — leave it.

## Watch-outs

- `crm_contacts` (plural) is the correct fileClass; the stock template ships
  `fileClass: crm_contact` (singular). Singular is always an error → fix to plural.
- Obsidian Sync and human edits may change notes during lint. Re-read before any
  fix, never clobber concurrent work, and stop on a conflict-copy error.
