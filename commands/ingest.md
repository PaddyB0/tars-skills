---
description: Ingest one raw external source into the knowledge wiki.
argument-hint: <path under Cowork/os/knowledge/raw/>
---

# /ingest <raw path>

Ingest a single **external** source (docs, threads, specs) into
`Cowork/os/knowledge/`. One source at a time, Patrick in the loop.

> Promoted to root `.claude/` under the one-OS-surface unification (Unified OS
> gameplan Phase 0). Distinct from **`/ingest-meeting`**, which propagates a
> `Meetings/` note into the CRM/PM wiki — this one is for the technical knowledge
> layer. Runs from the vault root; paths are repo-root-relative.

## Steps
1. Read the raw file at the given path (must live under `Cowork/os/knowledge/raw/`).
2. Discuss the key takeaways with Patrick before writing.
3. Write a one-source summary to `Cowork/os/knowledge/sources/`.
4. Create or update affected `Cowork/os/knowledge/{entities,concepts,runbooks,gotchas}/`
   pages. Cross-link with `[[page-name]]`; cite the backing `raw/` file for each claim.
5. On contradiction: keep both claims, mark `> ⚠️ CONTRADICTION:` with sources,
   surface to Patrick — never silently overwrite.
6. Update `Cowork/os/knowledge/index.md` (catalog line) and append to root `log.md`
   (`## [YYYY-MM-DD] ingest | Title`).

Every page opens with YAML frontmatter: `type, created, updated, tags, sources`.

> `/ingest` brings in **external** sources. To promote a lesson learned from
> **client work** into the knowledge layer, use `/distill`.
