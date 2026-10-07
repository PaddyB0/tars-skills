---
name: excel-design
description: Apply the canonical Excel report design contract - the TARS design system translated to .xlsx, with Impeccable-style deterministic linting. Tokens for typography, color, number formats, layout and charts, three styles (Instrument, Boardroom, Ledger), a client brand override, plus the TARS component set (KPI readout, segmented gauge, status badge, property row, table, card). Use for any client-facing or internal .xlsx report, "make this workbook look good", "standardize this Excel report", or before delivering any generated spreadsheet.
---

# Excel design

Every `.xlsx` report generated in this OS follows one visual contract:
`references/DESIGN.md`. It is the **TARS design system translated to a white,
printable canvas** — the same gunmetal ramp, indigo accent, mono
instrument-readout numerals, flat surfaces and segmented gauges — enforced by
the Impeccable method already piloted for TAR-OS UI (tokens documented once →
build against them → deterministic anti-pattern detection → polish).

File mechanics (openpyxl, reading/writing, conversion) stay with the `xlsx`
skill; this skill owns how the result looks. For TAR-OS *screen* work use
`tars-design` / `tars-ui` instead — same identity, different medium.

## Authority order

This skill is installed **globally** — it runs in any directory, not only the
TARS vault. Items 1, 2 and 4 are vault-relative: apply them when the working
directory is inside the TARS vault, and skip them silently when it is not.
`references/DESIGN.md` ships beside this file and always applies.

1. Root `CLAUDE.md` and the `vault-schema` skill (schema, Cowork boundaries —
   client work product lives under `Cowork/clients/<X>/outputs/`). *Vault only.*
2. An explicit client formatting requirement stated by the client or recorded
   in `Cowork/clients/<X>/MEMORY.md`, including an `Excel style:` pin (§9) and
   an `Excel brand:` override of at most three tokens (§10). *Vault only; outside
   the vault, take the style and override from the user directly.*
3. `references/DESIGN.md` — the contract, including its derived token table.
   **Always applies.** It is self-contained: every token is a literal hex, so
   the skill needs nothing else to produce a correct workbook.
4. `.obsidian/design-system/` — the upstream TARS identity. Consult it when
   the contract is silent on something (a component's intent, the voice rules).
   Never copy a dark-theme hex straight onto a white sheet; §0 of the contract
   explains why and gives the derivation rule. *Vault only.*

Outside the vault, do not guess at a missing authority and do not refuse the
work — item 3 alone is sufficient. Say which items you could not consult only
if the user asks about a choice one of them would have decided.

A generic aesthetic idea never overrides a higher authority. Do not invent a
new visual world per report. Pick one of the three styles; sameness within a
style is the point.

## Workflow

### 1. Shape

Before writing cells, state in one short block: audience, the one question the
report answers, the hero numbers, and the tab story (summary → report → data →
reference), and the style (§9): Instrument by default, Boardroom for a board
pack or executive one-pager, Ledger for a dense close pack, model or a
workbook that is mostly period sheets. Every style has period widths, so a
monthly tab never forces a style change. A report
with no hierarchy decision gets decorated, not designed.

### 2. Build against tokens and components

Read `references/DESIGN.md`. Resolve two things before writing cells:

- **Faces and sizes**: the style's pair and scale from §9. The sans carries
  all text *and every numeral*, and the mono carries instrument labels and the
  gauge only. Aptos is an M365 cloud font: if the recipient is on pre-2024
  Office, switch to the **Calibri + Consolas** fallback pair. Aptos Display,
  Aptos and Aptos Narrow are separate Excel families, so stay inside one pair.
  Never Inter: its digits are proportional and cannot align.
- **Colors**: the §2 palette, with any §10 brand override applied. Run the
  §10 checks on override tokens. A failing token keeps its default.

Then apply the tokens as literal formats and assemble the report from the
**§4 component set** — section label, KPI readout, segmented gauge, status
badge, property row, table, card. Do not hand-roll a new treatment for
something the component set already covers.

Two rules break most often, so check them explicitly: **numerals go in a
tabular-figure face** (the style's sans, never Inter — see §1 for the measurements), and
**progress is a segmented gauge, never a data bar**.

### 3. Audit

Run the deterministic lint on the produced file:

```bash
python "<skill-dir>/excel_lint.py" "<path/to/report.xlsx>"
```

Exit 0 = clean, 2 = findings, 1 = unreadable. Rules XL1-XL18; XL11 and XL12
label themselves heuristics. Fix true findings before recording an exception.
Exceptions are per-rule, per-sheet, with a stated reason (a raw data-dump tab
may waive XL11); never waive a whole workbook.
`not_run` is not `pass`; `waived` is not `pass`.

### 4. Polish and finish

- Uniform precision per column; units stated once in the subtitle.
- Delete ornament rather than adding it; whitespace over borders.
- Sentence case everywhere except mono uppercase instrument labels. Terse
  factual copy, no emoji — the TARS voice rule, unchanged.
- Charts: flat, accent hero series, `ink-3` context series, minimal chrome.
- Park every sheet at A1 / 100% zoom, summary tab active, print areas set,
  scaffolding sheets hidden, saved as `.xlsx`.
- Rerun the lint after polish; report the final exit state honestly.

### 5. Verify

When Excel or a renderer is available, open the file and look at it — a
passing lint is not visual verification. Check the title block, header band,
negative-number rendering, and that nothing overflows its column. When no
renderer is available, say so: visual verification is then `not_run`.

## Boundaries

- Inside the vault, deliverables go to `Cowork/clients/<X>/outputs/` for client
  work; never into a vault PM folder. Outside it, write where the user asks.
- This skill styles reports; it does not restructure a client's model or
  template logic (that is `/planning-template` and build-authority territory).
- Lint findings are informational; do not wire the exit code into hooks or CI.

## Maintenance

The contract is `references/DESIGN.md`; the detector is `excel_lint.py` with
tests in `tests/test_excel_lint.py` (`python -m pytest tests/ -q` from the
skill directory). A rule change edits both together, tests first.

If `.obsidian/design-system/tokens/` changes upstream, re-derive the §2 table
rather than eyeballing it: preserve each token's hue and saturation, re-anchor
lightness for white, and hold every text token at >= 4.5:1 contrast on white,
`band` and `accent-fill`, with
`positive`/`negative` separated >= 1.5:1 in grayscale. Never edit the design
system itself from here — it is `.obsidian/`, off limits per root `CLAUDE.md`.
