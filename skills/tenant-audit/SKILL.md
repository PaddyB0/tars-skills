---
name: tenant-audit
description: Read-only design audit of one Datarails tenant. Layer 1 runs the mec-table-validation skill, layer 2 runs the eight FinanceOS anti-pattern checks (AP1 to AP8) through dr-cli reads, and the result is one pass/fail/not_run row per check with quoted evidence. Writes nothing to the tenant. Use when the user says "audit this tenant", "is this build correct", "tenant health check", "run the anti-pattern checklist", "/tenant-audit <client>", or before calling any Datarails tenant build correct.
---

# /tenant-audit

A read-only design audit of one Datarails tenant, in two layers.

1. **Layer 1:** the `mec-table-validation` skill. Invoke it through the Skill
   tool with the same `--server` key. Do not restate or re-run its checks by
   hand. Its own summary line becomes one report row.
2. **Layer 2:** the eight anti-pattern checks in
   [references/anti-patterns-checklist.md](references/anti-patterns-checklist.md),
   AP1 to AP8.

**This skill writes nothing to the tenant.** A fix is a separate request with
its own authority.

---

## Pre-flight

1. `dr whoami --server <key> [--account <email>]`. Echo the org back and stop if
   it is not the tenant the user named.
2. When a client is named, resolve `Cowork/clients/<Client>/` from the TARS
   company note (`CRM/Clients/<Client>.md`, key `cowork_client`). Check the
   client folder's `CLAUDE.md` for a name collision before reading anything.
   Read `Cowork/clients/<Client>/MEMORY.md`, which AP5 and AP6 use.
3. Read `Cowork/os/knowledge/index.md` for gotchas relevant to what the tenant
   runs.
4. Load `/vault-schema` only if a vault note will be written. By default none is.

---

## Recipe

1. Run layer 1. Record its summary line and its own verdict.
2. Run `dr templates list` once and pick the fact tables in scope (actuals,
   plan, headcount, cash). Name them in the report.
3. For each section AP1 to AP8 in the checklist, run the reads listed under each
   indicator, decide each indicator from the stated hit rule, then apply the
   section's verdict rule. The checklist owns the commands, the hit evidence and
   the verdict rules. Do not add commands it does not list.
4. Collect every `judgment` question and ask the operator in one batch after the
   reads. An unanswered one leaves its indicator `not_run`.

Commands allow-listed in `.claude/settings.json` run without a prompt:
`dr templates list|get|aggregate|distinct|sample`, `dr datamappers list|get`,
`dr lut list|data|unmapped`, `dr filebox list|get|versions|sheets`,
`dr dynamic-ranges list|get`, `dr functions list|get`, `dr scans status`,
`dr collection-processes list`. The other reads the checklist cites
(`dataflow get`, `calcmodels list`, `metrics list`, `dashboards list`,
`widgets list|get`, and similar) are read-only but prompt for approval.

---

## Output

One report, one row per check:

| Check | Verdict | Evidence |
|---|---|---|
| MEC | `pass` / `fail` / `not_run` | mec-table-validation summary line, quoted |
| AP1 System Silos | `pass` / `fail` / `not_run` | the command and the output lines that decided it |
| ... AP2 to AP8 | | |

- Each verdict is exactly `pass`, `fail` or `not_run`. `not_run` is never
  reported as `pass`, and a section with one `not_run` indicator and no hit is
  `not_run`.
- List open `judgment` questions under the table.
- Default: write the report to chat.
- With `--report`: also write it to
  `Cowork/clients/<Client>/outputs/tenant-audit-<YYYY-MM-DD>.md`.

---

## Guard rails

- Read-only. Never run any `dr ... update`, `create`, `delete`, `bind` or
  `rescan`, and never trigger a recalculation.
- Stop on a 403 or a wrong tenant. Report what ran and mark the rest `not_run`.
- Never fabricate a value a command did not return. Quote output, do not
  paraphrase numbers.

---

## Related

- [[FinanceOS Summary for LLMs]] — the platform map
- [[FinanceOS Design Anti-patterns]] — the source of every AP check
- [[FinanceOS Design Validation]] — the question bank that confirms a remediation worked
- `Cowork/os/knowledge/index.md` — gotchas and runbooks
