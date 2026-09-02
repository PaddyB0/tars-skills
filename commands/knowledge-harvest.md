---
description: Read-only harvest of recent client-work lessons into scrubbed, deduplicated /distill candidates without promoting or writing knowledge.
argument-hint: "[<client folder name> | --days <N>]"
---

# /knowledge-harvest [<client> | --days <N>]

Identify a small number of genuinely reusable lessons from recent engagement work
and draft safe candidates for Patrick to approve. This is the observation and
proposal step before `/distill`; it never performs `/distill`.

Read root `CLAUDE.md`, `Cowork/CLAUDE.md`,
`.claude/commands/distill.md`, and `Cowork/os/knowledge/index.md` before
evaluating candidates.

## Non-negotiable boundary

The entire run is read-only:

- Do not create or update knowledge pages, the knowledge index, `log.md`, client
  memory, notes, tasks, or any other file.
- Do not invoke `/distill`, `/ingest`, `/handoff`, Git mutation, or an external
  write-capable connector.
- Do not copy raw client data, client names, people, account or tenant IDs,
  workbook names, URLs, credentials, or client-specific figures into a proposed
  reusable draft.
- Do not inspect `Cowork/clients/*/inputs/` automatically. Raw inputs are
  unnecessary for candidate discovery and carry the highest disclosure risk.
- Do not promote an unverified hypothesis, a client-status update, a one-off
  workaround with no mechanism, or a lesson already covered by the knowledge
  layer.
- On contradiction with existing knowledge, preserve both claims in the report,
  mark the candidate **CONTRADICTION — Patrick review required**, and never
  choose a winner.
- Return candidates in chat only. Do not file the harvest report.

Private source paths may appear only in a clearly labeled **Review-only evidence**
field so Patrick can trace the candidate. They must not appear inside the scrubbed
draft.

## 1. Pin the harvest window

Use the real local date in `America/Edmonton`. Default to the preceding seven
calendar days; `<client>` narrows the run to one exact client folder, while
`--days <N>` changes the lookback.

Record branch, HEAD, and `git status --short`, but do not pull, fetch, or clean.
Use Git history as primary recency evidence:

```bash
git log --since="<N> days ago" --name-only \
  --format="commit %H %cI %s" -- \
  ":(glob)Cowork/clients/*/MEMORY.md" \
  ":(glob)Cowork/clients/*/outputs/**"

git status --short -- \
  ":(glob)Cowork/clients/*/MEMORY.md" \
  ":(glob)Cowork/clients/*/outputs/**"
```

File mtimes are weak evidence and may only break ties. Include relevant dirty
client files as an unstable worktree surface; if one changes twice while being
read, skip it and report that it was unstable.

From the resulting client folders, prioritize substantive changes to:

- `MEMORY.md`;
- text-based deliverables and investigation notes under `outputs/`;
- client-local notes explicitly referenced by those artifacts.

Ignore `.gitkeep`, raw inputs, generated binaries, duplicate exports, and changes
that only update timestamps or formatting. Review at most five client folders per
run, ranked by substantive evidence. Name any additional folders as deferred.

## 2. Find candidate lessons

For each reviewed client, ask:

1. Would this help a different client facing the same class of problem?
2. Is there evidence for the mechanism, not merely a record of what was done?
3. Can the lesson remain useful after every client identifier and figure is
   removed?
4. Is it novel relative to the current knowledge index and relevant pages?
5. Is it stable enough to guide future work, with its limits stated?

Classify the appropriate destination:

- `runbooks/` — repeatable procedure;
- `concepts/` — transferable FP&A or Datarails mechanic;
- `gotchas/` — specific failure mode, cause, and correction;
- `entities/` — durable system or data-source knowledge.

Reject candidates that are:

- client status, politics, commitments, or project-management state;
- a client-specific mapping, naming convention, ID, workbook, or amount;
- a generic lesson with no concrete mechanism;
- already captured without meaningful new evidence;
- dependent on confidential details that cannot be removed;
- contradicted by evidence and not ready for Patrick to adjudicate.

Prefer fewer strong candidates over many thin pages.

## 3. Deduplicate and test the generalization

For each survivor:

1. Read the most relevant existing knowledge pages, not just their index lines.
2. Label it `NEW`, `EXTEND <existing page>`, `DUPLICATE — reject`, or
   `CONTRADICTION`.
3. Replace client-specific nouns with stable system concepts.
4. Replace exact figures with the transferable relationship or validation rule.
5. Remove all people, tenant/account IDs, URLs, filenames, and customer-specific
   configuration.
6. State where the lesson does **not** apply.
7. Search the proposed scrubbed draft for identifiers from its review-only source
   before returning it. If complete scrubbing is doubtful, reject it.

Score each survivor from 0–2 on:

- transferability;
- mechanism/evidence;
- novelty;
- scrubability.

Only recommend candidates scoring at least 6/8. A contradiction may be surfaced
below threshold but cannot be recommended for promotion.

## 4. Draft candidates without promoting them

Return no more than five candidates. The proposed page content must be scrubbed;
source traceability stays outside it.

```markdown
# TARS Knowledge Harvest — YYYY-MM-DD

**Window:** <dates or client> · <HEAD SHA> · <N client folders reviewed>
**Result:** <N recommend> · <N investigate> · <N rejected as duplicate/client-only>

## Recommend for supervised `/distill`

### 1. <scrubbed working title>
- Disposition: NEW | EXTEND `[[existing-page]]`
- Destination: `runbooks|concepts|gotchas|entities/<slug>.md`
- Score: <0–8>
- Review-only evidence: `<private client path>` — <general evidence description,
  without quoting sensitive data>
- Why transferable: <one sentence>
- Redactions applied: <categories removed>
- Limits: <where it does not apply>

#### Scrubbed draft outline
- Problem/symptom: ...
- Mechanism/cause: ...
- Procedure/correction: ...
- Verification: ...
- Related knowledge: `[[...]]`

#### Proposed scrubbed frontmatter
`type`, `created`, `updated`, `tags`, and a non-identifying `sources` description.

## Investigate before distilling
- **<candidate>** — <missing evidence or contradiction requiring Patrick>

## Rejected
- **<lesson>** — DUPLICATE `[[page]]` | CLIENT-ONLY | UNVERIFIED | NOT SCRUBBABLE

## Deferred client folders
- <folder not reviewed because of the five-folder cap>

## Patrick's decisions
1. Approve `/distill <client>` for candidate <N>?
2. <contradiction or general/specific boundary decision>
```

Omit empty sections. Do not include raw excerpts. The recommended daylight action
is a supervised `/distill <client>` run, one client at a time, after Patrick
confirms the general/specific split.
