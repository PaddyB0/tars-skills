---
name: os-audit
description: Read-only drift, freshness, routing, organization, and context-health inspection with one named report output. Use when someone asks to run an OS audit, check TAR-OS or another AIOS for stale or outdated data, verify routing points at real files, find duplicate or bloated folders, clean up or organize a project, check for context poisoning/bloat/confusion/clash, or says "os audit", "is my setup stale", "run a data audit", "my project root is a mess", or "my agent keeps missing things that are there".
---

# OS Audit — is the AIOS still true?

Treat operating manuals, indexes, and wikis as claims about what exists and what
is current. Check every claim against reality. Structure problems are loud;
freshness problems are silent. When an agent keeps forgetting things, it may be
faithfully reading a frozen index.

The evidence collection is `R0` and read-only. The workflow as a whole is `R1`
only because invoking it pre-authorizes one reversible output at the exact path
`audits/os-audit-YYYY-MM-DD.md`, with the date resolved before work begins and
recorded in `scope.writePaths`. Never fix, move, rename, or delete anything
during the audit. If the caller requires a fully read-only run, the report path
is unavailable, or that exact path was not named in the task contract, print
the report in chat and do not write a file. Make fixes only after separate user
approval.

Work on any agentic project. Detect operating manuals, indexes, and wikis by
role rather than assuming exact paths or names.

## Context

- Use today's real date for all freshness math.
- Audit the current project root, or the optional subfolder the user supplies.

## Classification lenses

Tag every finding with at least one context failure mode:

- **Poisoning** — false information is loaded and trusted as true.
- **Bloat** — excess context causes the model to lose the thread.
- **Confusion** — needed context is missing or off-topic context is present.
- **Clash** — two pieces of context contradict, usually old versus new.

If a finding feeds none of the four, call it cosmetic and rank it last.

Also classify context by when it should load:

- **Expertise context** — stable operating knowledge needed on every call.
- **Situational context** — live, specific information fetched only when needed.

## Step 0 — Prior report and recent evidence

1. Look for earlier reports in `audits/os-audit-*.md`. If one exists, read the
   most recent and include a `Since last audit` section: fixed, worse, and new.
2. If an audit ran within the last week, build a small reuse ledger from its
   cited paths, dates, counts, and claims. Reuse an item only after a cheap check
   confirms the path still exists and the relevant source has not changed.
   Re-run only volatile, changed, missing, or previously unresolved evidence.
3. Perform one shared deterministic discovery pass for the project root,
   operating-manual candidates, index candidates, top-level directories, prior
   report, and git/ignore state. Reuse those facts across checks and workers.

## Execution

Treat subagents as evidence collectors. The parent owns cross-checking,
failure-mode tags, verdicts, and the final report.

For a project under 100 folders, run the checks yourself in order. For a larger
project, use at most three workers with `max_parallel: 3`:

1. Routing integrity + Index truth.
2. Freshness + Context placement.
3. Bloat/organization + Hygiene/silent failures.

Use the economy tier with low effort for first-pass workers and the standard
tier with medium effort for parent synthesis. Do not use frontier/high effort
for routine audit collection. Permit one targeted standard-tier escalation when
direct sources conflict, a possible RED security/routing finding cannot be
confirmed, deterministic output is unavailable or truncated, or semantic
ambiguity would change a RED/YELLOW verdict.

Give each worker a self-contained packet of at most 1,200 words containing:

- project root, audit date, and assigned check text;
- discovered manual/index paths and shared deterministic facts;
- prior-report evidence eligible for reuse;
- explicit scope and read-only authority; and
- the return keys `coverage`, `reused_evidence`, `findings`,
  `unresolved`, and `commands_run`.

Pass paths rather than copied file bodies. Workers read cited files directly,
must not fork the full conversation, and must not spawn subagents. Collapse
repeated instances into a count plus at most three representative paths.

Stop a worker when every assigned item is evidenced, validly reused, or marked
unresolved. Do not broaden into adjacent repositories, external systems, or
unassigned checks. Do not retry merely because a check found nothing.

If the one targeted escalation cannot resolve disputed evidence, preserve it
under `unresolved` or `Questions for you`; never repeat the same search loop.

If there is no operating manual and no index, make that the number-one finding.
Mark Routing and Index checks RED with: `no routing layer exists: your agent is
navigating by guesswork`. Recommend creating an operating-manual router first,
then continue with Checks 3–5.

### Check 1 — Routing integrity

1. Read the operating manual (`CLAUDE.md`, `AGENTS.md`, or equivalent). Extract
   every referenced path, folder, file, and routing-table entry; verify each
   exists.
2. List top-level directories and compare them with the manual. Flag active,
   unmapped directories.
3. Flag misroutes where a referenced path exists but is not where current data
   lives.
4. Spot-check hardcoded paths inside skills and agent definitions.
5. If persistent memory exists, verify every index entry resolves and flag
   memory files missing from the index.

### Check 2 — Index truth

1. Find index files such as `_index*.md`, `INDEX.md`, catalog sections,
   hot-cache files, and summaries. Diff their entries against disk in both
   directions: phantoms and orphans.
2. Verify claimed counts against reality.
3. Verify freshness claims against content dates. An allegedly recent index
   whose newest entry is old is actively misleading.

### Check 3 — Freshness

1. Identify recurring data sources: transcript pulls, meeting ingests, API
   exports, wikis, analytics dumps, and anything with dated files or refresh
   scripts. Compare the newest artifact with each source's natural cadence.
2. Classify each feed:
   - **FRESH** — within one cycle.
   - **DRIFTING** — one cycle behind.
   - **FROZEN** — more than one cycle behind while the OS implies it is current.
   - **RETIRED?** — more than about two months dead; ask whether it stopped on
     purpose.
   - **ON-DEMAND** — no natural cadence; note the last run without calling it
     stale.
3. Check both layers when raw data is later ingested into knowledge. Report the
   raw date and ingested date; their gap is un-queryable knowledge.
4. Check hot caches and summaries for numbers and threads older than their
   claimed refresh cycle.
5. Scan memory notes for provably stale time-dependent facts: counters,
   snapshots, statuses, and future events now in the past.
6. State the effective date through which the AIOS's ingested knowledge is
   current.

### Check 4 — Bloat, duplication, and organization

1. Find content or purposes duplicated across locations. Recommend a canonical
   copy.
2. Identify old one-off folders and finished point-in-time work as archive
   candidates, not deletion candidates.
3. Find scratch contamination: temp files, response dumps, caches, and empty
   stubs in the knowledge tree.
4. Word-count always-loaded files and flag excessive growth.
5. Find violations of placement rules declared by the manual.
6. Audit root hygiene. Classify loose root files by role and recommend an
   existing home. Before recommending a move, search for live references and
   list any paths that make it move-with-caution.
7. Pick three recent artifacts and navigate to each like a human using only
   folder names. Flag unintuitive paths and ambiguous folder names.

### Check 5 — Hygiene and silent failures

1. For git repositories, verify `.env`, OAuth, and credential files are ignored
   and untracked. Scan tracked files for exported personal data that should not
   be in history. For non-git projects, scan the tree directly and flag the lack
   of history, rollback, and an ignore layer.
2. Find dead capabilities: incorrectly named skill files, missing or empty
   frontmatter descriptions, and agents referencing missing models or paths.
3. Find orphaned memory folders, empty directories, and zero-byte files.
4. Verify that declared recurring processes have real hooks or schedules.
   Explicitly identify manual-only cadence as a likely cause of frozen feeds.

### Check 6 — Context placement

1. Inventory always-loaded expertise files and flag situational facts baked into
   them. Each is both future poisoning and per-session bloat; recommend a
   pointer to the live source rather than a refreshed copy.
2. Find stable expertise buried in situational stores and recommend promoting
   it to the manual or rules layer.
3. Check whether the manual defines precedence when stores disagree. If not,
   recommend: `X is the source of truth for Y; everything else points at it.`
4. Spot-check three to five important facts. Flag duplicates stored at multiple
   ages and identify the oldest copy as the poisoning risk.

## Output

Print the report in chat. Save it to the pre-authorized
`audits/os-audit-YYYY-MM-DD.md`, creating `audits/` if needed, only when that
exact path is present in `scope.writePaths`. This report is the audit's only
write. Otherwise keep the run fully read-only and return the report only in
chat.

```markdown
# OS Audit — {date}

**Knowledge current through: {effective ingested-layer date from Check 3}**

| Check | Verdict | Worst finding |
|---|---|---|
| Routing integrity | GREEN/YELLOW/RED | ... |
| Index truth | GREEN/YELLOW/RED | ... |
| Freshness | GREEN/YELLOW/RED | ... |
| Bloat/duplication | GREEN/YELLOW/RED | ... |
| Hygiene | GREEN/YELLOW/RED | ... |
| Context placement | GREEN/YELLOW/RED | ... |

## Failure-mode exposure

| Mode | Exposure | Driven by |
|---|---|---|
| Poisoning (false) | HIGH/MED/LOW | ... |
| Bloat (too much) | HIGH/MED/LOW | ... |
| Confusion (wrong or missing) | HIGH/MED/LOW | ... |
| Clash (contradictory) | HIGH/MED/LOW | ... |

## Since last audit
{Omit on first run. Otherwise: fixed / worse / new.}

## What would make your agent wrong-answer you today
{Two to four bullets.}

## Findings by check
{Every finding names a concrete path and ends with one or more failure-mode tags.
Include: feed | raw date | ingested date | cadence | verdict | what's missing.}

## Questions for you
{Ask about RETIRED? feeds and facts only the owner can resolve.}

## Fix list (batched, await approval)
- Batch A — security + dead capabilities
- Batch B — routing + index reconciliation + root cleanup
- Batch C — data catch-up + officially retire dead feeds
- Batch D — durability via hooks, schedules, or rituals
```

## Verdict rules

- **RED** — at least one finding could cause wrong answers today: a frozen
  pipeline, lying index, dead or misrouted route, tracked secret, or stale fact
  in an always-loaded file.
- **YELLOW** — drift that could become RED: unindexed folders, duplicates, bloat,
  or missing precedence.
- **GREEN** — checked and clean.

Confirmed retired feeds stop counting toward RED only after the OS stops implying
they are current. A first audit of a used AIOS should rarely be all green.

Set a failure mode to HIGH when a RED finding feeds it, MED when only YELLOW
findings feed it, and LOW when nothing does.

## Evidence rules

- Prefer dated filenames and content dates. Treat mtimes as weak evidence because
  git and cloud-sync tools can rewrite them in bulk.
- Treat a stale local snapshot of live external data as a labeling problem, not a
  freshness problem. Recommend labeling the live source of truth.
- Never fix findings during the audit, even trivial ones.
- Suggest re-running quarterly or after a major reorganization.
- If the project has a separate structural AIOS audit, mention it as a companion;
  otherwise omit that reference.
