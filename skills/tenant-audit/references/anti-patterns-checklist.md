# Anti-pattern checklist (AP1 to AP8)

The runnable form of the table in [[FinanceOS Design Anti-patterns]]. One section
per anti-pattern, in the note's order. The note owns the reasoning and the fixes.
This file owns only what to read, what counts as a hit and the verdict.

Conventions for every section:

- Every `dr` command takes `--server <key>`, plus `--account <email>` when more
  than one identity is stored. They are omitted below for length.
- `<tid>` is a template (table) id from `dr templates list`. `<doc>` is a filebox
  document id, `<vid>` a version id, `<mid>` a datamapper id, `<lid>` a lookup id.
- An indicator marked `judgment` cannot be decided from command output. Gather
  the listed reads, then ask the operator the stated question. An unanswered
  `judgment` indicator is `not_run`.
- Verdicts are `pass`, `fail` or `not_run`. A section is `not_run` when any
  command it needs failed or was refused and no other indicator already proves
  a hit. `not_run` is never reported as `pass`.
- Quote the command output that proves each hit. Never infer a value a command
  did not return.

---

## AP1 System Silos

Definition: the same finance concept has a separate table per source system or
per entity instead of one table for the concept.

Indicators (derived from the Example and Problems subsections):

1. Two or more tables for one concept whose names differ only by a source
   system or entity token (`TB_NetSuite`, `TB_QBO`, `TB_EntityA`).
   Read: `dr templates list`.
2. A consolidation table fed by a calc model over the per-source tables.
   Read: `dr calcmodels list`, then `dr dataflow get <tid>` on the suspected
   consolidation table. Hit when its inputs are the tables from indicator 1.
3. Parallel chart-of-accounts lookups rebuilt on each per-source table.
   Read: `dr lut list --table <tid>` on each table from indicator 1. Hit when
   each carries its own COA lookup.
4. `judgment` One entity fed by both an integration sync and a manual GL upload.
   Reads: `dr integrations list`, `dr filebox list`, `dr datamappers list --table <tid>`.
   Ask the operator: "Is any entity loaded both by the integration and by a
   manual file? Which one wins?"

Verdict: `fail` if indicator 1 or 2 hits, or indicator 4 is confirmed. `pass`
if each finance concept has one table and indicator 4 is answered no.

Source: ([[FinanceOS Design Anti-patterns#Anti-pattern: System Silos]])

---

## AP2 The Kitchen Sink

Definition: every export column is mapped and aliased, so the semantic layer
carries ETL helpers, source-system ids and columns nobody reads.

Indicators (derived from the Example, Problems and Solution subsections):

1. Field count against aliased-field count, reported for each fact table.
   Read: `dr templates get <tid> --json`, counting `fields[]` and the fields
   with a non-empty `alias`. Context only, never a hit on its own.
2. Sibling columns for one meaning: several amount columns (`Amt`, `Amount`,
   `Debit_Credit_Net`) or several date columns on one table.
   Read: `dr templates get <tid>`.
3. Silent zeros: the `amount` alias is missing, or it sits on a field that sums
   to zero while a sibling amount field does not.
   Read: `dr templates get <tid> --json` for the alias, then
   `dr templates aggregate <tid> --group-by <reporting date field> --metric <field>:SUM`
   once for the aliased field and once for each sibling from indicator 2.
4. ETL helpers carry an alias: import timestamps, batch ids, row hashes, source
   internal ids, mapper fill helpers or flags.
   Read: `dr templates get <tid> --json`.

Verdict: `fail` if indicator 2, 3 or 4 hits. `pass` if none does. Indicator 1
is reported as counts in the evidence either way.

Source: ([[FinanceOS Design Anti-patterns#Anti-pattern: The Kitchen Sink]])

---

## AP3 Department Silos

Definition: accounting, FP&A and operations each keep their own version of a
shared concept, so the tenant mirrors the org chart instead of the business.

Indicators (derived from the Example and Problems subsections):

1. More than one account list: fact tables enrich the account key from
   different reference sources.
   Read: `dr templates list`, then `dr lut list --table <tid>` on each fact
   table (actuals, budget, headcount). Hit when the account lookups point at
   different source tables or documents.
2. The plan table's account keys do not match the actuals table's account keys.
   Read: `dr templates distinct <tid> --field <account field>` on both tables,
   or one sweep with `dr metrics dimensions suggestions profile --json`, whose
   value-overlap groups and `near_misses` show keys that should match and do not.
   Hit when the plan keys are not a subset of the actuals keys.
3. Department or cost-center codes that match across no two tables.
   Read: same commands as indicator 2, on the department field.
4. `judgment` No named owner for a shared dimension.
   Ask the operator: "Who owns the chart of accounts and the department list,
   and who approves a reclass?"

Verdict: `fail` if indicator 1, 2 or 3 hits. Indicator 4 answered "nobody" is
also `fail`. `pass` if all four are clear.

Source: ([[FinanceOS Design Anti-patterns#Anti-pattern: Department Silos]])

---

## AP4 The God Object

Definition: one table holds several distinct finance concepts, such as ledger
movements, period balances, plan lines, headcount and cash side by side.

Indicators (the note's Indicators list):

1. Many fields null for most rows.
   Read: `dr templates sample <tid> --rows 1000 --json`, counting nulls per
   field. Hit when a field is null on more than half the sampled rows and is
   populated only for one class of row.
2. A `record_type` or `measure` column that changes what `amount` means.
   Read: `dr metrics suggestions profile --tables <tid> --json` for
   `row_grain.reads_as`, then `dr templates distinct <tid> --field <type field>`
   and `dr templates aggregate <tid> --group-by <type field> --metric <amount field>:SUM`.
   Hit when the type values split movements from balances, plan or headcount.
   `reads_as: "unknown"` is a real answer to quote, not a pass.
3. `judgment` `ignore_zeros` or a header filter dropping rows that were real.
   Read: `dr datamappers list --table <tid>`, then `dr datamappers get <mid> --json`
   for `ignore_zeros`, header filters, `filter_out_regex` and `mandatory_field`.
   Ask the operator: "Do the rows these settings drop carry meaning, for
   example zero-movement balance-sheet lines?"
4. `judgment` Business rules that need "if balance sheet then ... else ..." in
   every formula.
   Reads: `dr calc-vals list --table <tid>`, `dr functions list` and
   `dr functions get <id>`, and the calc fields in `dr datamappers get <mid> --json`.
   Ask the operator: "Does every formula on this table branch on account class
   to decide what the amount means?"

Verdict: `fail` if indicator 1 or 2 hits, or indicator 3 or 4 is confirmed.
`pass` if all four are clear.

Source: ([[FinanceOS Design Anti-patterns#Anti-pattern: The God Object]])

---

## AP5 The Golden Hammer

Definition: one FinanceOS tool is used for every problem because it is the one
the implementer knows.

Indicators (derived from the Examples and Problems subsections):

1. Calc models that depend on each other, so one recomputes before its input
   finishes (refresh races).
   Read: `dr calcmodels list`, then `dr dataflow get <tid>` on each model's
   source table. Hit when one model's output table is another model's input.
2. An account rollup written as a long nested mapper expression instead of a
   lookup.
   Read: `dr datamappers get <mid> --json`, calc-field formulas. Hit when a
   calc field branches on literal account values to assign a rollup line.
3. A lookup carrying pre-calculated values that is re-uploaded every period.
   Read: `dr lut list --table <tid>`, `dr lut data <doc> <lid>`, and
   `dr filebox versions <doc>` on the lookup's source document. Hit when the
   value columns are derived numbers and the document gets a new version each
   period.
4. `judgment` The forecast roll-forward is maintained by copying workbook
   formulas each cycle.
   Read: `dr filebox list`, `dr dynamic-ranges list --table <tid>`.
   Ask the operator: "Is the forecast rolled forward by copying formulas in the
   workbook each cycle?"
5. A recurring dr-cli operation the customer cannot run.
   Vault read: `Cowork/clients/<Client>/MEMORY.md`. Hit when a monthly or
   per-cycle step is recorded as run by us through dr-cli.

Verdict: `fail` if any indicator hits or a `judgment` indicator is confirmed.
`pass` if all five are clear.

Source: ([[FinanceOS Design Anti-patterns#Anti-pattern: The Golden Hammer]])

---

## AP6 Action Sprawl

Definition: the ways users change the tenant are many narrow operations instead
of a few that match how finance works.

Indicators (the note's Indicators list, plus indicator 5 from its Problems table):

1. More than one submission per department per cycle to complete one budget.
   Read: `dr collection-processes list --scenario Budget` and
   `dr documents split list`. Hit when one department has more than one
   collection process or split child for the same cycle.
2. A KPI widget per number instead of one metric reused.
   Read: `dr dashboards list`, `dr widgets list --dashboard <id>` per
   dashboard, `dr metrics list`. Hit when the same number appears as separately
   built widgets on two or more dashboards and no metric of that name exists.
3. `judgment` A budget split into more outputs than there are reviewers.
   Read: `dr documents split list` for the child count.
   Ask the operator: "How many people review this budget?" Hit when outputs
   exceed reviewers. The cap is 50 outputs per split.
4. A client MEMORY.md with many "changed X on date Y" lines and no stated
   operation.
   Vault read: `Cowork/clients/<Client>/MEMORY.md`. Hit when tenant changes are
   logged as prose lines without the operation and its parameters.
5. A planning dynamic range filtered on a rolling submission date.
   Read: `dr dynamic-ranges list --table <tid>`, then
   `dr dynamic-ranges get <range_id> --table <tid> --json` for `filters`. Hit
   when a filter windows on a submission or upload date.

Verdict: `fail` if indicator 1, 2, 4 or 5 hits, or indicator 3 is confirmed.
`pass` if all five are clear.

Source: ([[FinanceOS Design Anti-patterns#Anti-pattern: Action Sprawl]])

---

## AP7 The Time Machine

Definition: history is modeled as separate tables, fileboxes or mappers instead
of as versions and scenario fields on one table.

Indicators (the note's Indicators list, plus indicator 5 from its Problems table):

1. Table names with years or the word legacy, or a filebox per year or cycle.
   Read: `dr templates list`, `dr filebox list`. Hit on a name carrying a year,
   a quarter or cycle label, or `legacy`.
2. Several mappers bound to one document, one of them stale.
   Read: `dr datamappers list --table <tid>`, `dr datamappers get <mid> --json`
   (`mapped_documents_ids`) per mapper, then `dr datamappers processed-versions <mid>`
   and `dr filebox versions <doc>`. Hit when two mappers cover one document and
   one has not processed the latest version.
3. Forecast rows appearing twice just past the actuals boundary.
   Read: `dr templates aggregate <tid> --group-by <reporting month field> --group-by <scenario field> --metric <amount field>:COUNT`.
   Hit when the first forecast months after the last actuals month carry about
   twice the row count of the months around them.
4. `judgment` A dashboard that needs its table id changed every January.
   Read: `dr dashboards list`, `dr widgets get <id>` on the main widgets.
   Ask the operator: "Do these dashboards get repointed to a new table each
   year?"
5. An active version that never reaches the table because its include flag is
   off.
   Read: `dr filebox versions <doc>` against `dr filebox versions <doc> --included`,
   then `dr scans status <tid>`. Hit when an active current-period version is
   missing from the included list.

Verdict: `fail` if indicator 1, 2, 3 or 5 hits, or indicator 4 is confirmed. A
new filebox for a changed upload format is the one legitimate fork; confirm it
with the operator before counting indicator 1. `pass` if all five are clear.

Source: ([[FinanceOS Design Anti-patterns#Anti-pattern: The Time Machine]])

---

## AP8 The Misnomer

Definition: tables, fields and widgets carry vague, source-system or misleading
names, so the controller and the agent have to guess.

Indicators (the note's Indicators list):

1. `judgment` "Which date is this?" asked in every working session.
   Read: `dr templates get <tid> --json`. Note every Date field and whether its
   name or alias says its role.
   Ask the operator: "Does the controller ask which date a field is?"
2. `Credit` pre-signed negative on one source and positive on another.
   Read: `dr templates aggregate <tid> --group-by <entity or source field> --metric <credit field>:MIN`
   and the same with `:MAX`. Hit when one group is never positive and another
   is never negative.
3. A dynamic range returns an empty set because a property name is spelled
   differently.
   Read: `dr dynamic-ranges list --table <tid>`,
   `dr dynamic-ranges data <range_id> --table <tid> --json`, then
   `dr dynamic-ranges get <range_id> --table <tid> --json` against
   `dr templates distinct <tid> --field <filter field>`. Hit when a range
   returns no rows and a filter value is absent from the field's distinct
   values.
4. A key column renamed in a mapping file, so the join silently matches nothing.
   Read: `dr lut list --table <tid>` for the lookup keys, `dr filebox versions <doc>`
   and `dr filebox preview <vid>` for the source sheet headers, then
   `dr templates aggregate <tid> --group-by <lookup value field> --metric <amount field>:COUNT`.
   Hit when a key is missing from the headers or every row lands in the null
   group. `dr lut unmapped` showing zero is not an all-clear.

Verdict: `fail` if indicator 2, 3 or 4 hits, or indicator 1 is confirmed.
`pass` if all four are clear.

Source: ([[FinanceOS Design Anti-patterns#Anti-pattern: The Misnomer]])
