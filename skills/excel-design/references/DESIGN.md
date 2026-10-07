# Excel report design contract

The single visual authority for every `.xlsx` report generated in this OS.

Two sources feed it. The **TARS design system** (`.obsidian/design-system/`)
supplies identity — the gunmetal neutral ramp, the indigo accent, mono
instrument labels, flat surfaces, hairline seams, segmented gauges. The concepts in [pbakaus/impeccable](https://github.com/pbakaus/impeccable)
supply method — tokens documented once, deterministic anti-pattern detection,
restraint over decoration. `excel_lint.py` enforces the testable subset; this
file is the full contract.

The contract has three layers. The core, §0–§8, binds every workbook. A
**style** (§9) sets type, row height, column widths and three treatments. A client
**brand override** (§10) may then change three color tokens. Nothing else
varies between deliverables.

---

## 0. Why this is not the TARS palette verbatim

TARS is **dark-only**. There is no `.theme-light` block in
`design-system/tokens/colors.css`; the app background is `#17181c` and the
indigo accent sits at 68% lightness to glow against it. An Excel report is a
white document that gets printed. Dropping those hexes onto white fails
contrast outright.

So the tokens below are **derived, not copied**: each preserves the TARS hue
and saturation family and re-anchors lightness for a white canvas. The
gunmetal ramp keeps TARS hue 228 at its real 11–14% saturation. The accent
keeps the indigo hue 234. Every text token clears WCAG AA (>= 4.5:1) on every
fill it sits on: white, `band` and `accent-fill`. White alone is not enough,
because labels sit inside tiles and badges.

One further constraint TARS never faces: **these reports get printed in black
and white.** Favorable and unfavorable must stay tellable apart with the color
gone, so `positive` and `negative` are separated in luminance as well as hue
(1.52:1 grayscale, verified). Color is never the only channel anyway — see §3.

---

## 1. Typography

TARS pairs a sans with **mono instrument readouts**. That motif transfers to
Excel in part, and the reason is measurable.

**A numeric column needs tabular (fixed-width) figures, not monospace.** Excel
right-aligns numbers so the last digit always lines up; the digit *columns* to
its left line up only when every digit has the same advance width. Monospace
additionally forces the **comma and period** to full digit width, which buys
nothing and costs a great deal of room.

Measured with PIL, `(1,234,567)` at 10pt:

| Face | Tabular? | Width | Zero | Note |
|---|---|---|---|---|
| Calibri | yes (20.0) | 46.7pt | plain | fallback pair |
| Aptos Narrow | yes (20.0) | 46.9pt | plain | Ledger's face |
| **Aptos Display** | **yes (21.0)** | **47.2pt** | **plain** | **the body and numeral face** |
| Aptos | yes (21.0) | 48.7pt | plain | Boardroom's face |
| Arial | yes | 50.5pt | plain | — |
| Inter | **no (16.0-26.0)** | 53.8pt | plain | cannot align a column |
| Consolas | yes | 60.5pt | slashed | fallback mono |
| **Aptos Mono** | yes (24.0) | 66.0pt | slashed | **instrument labels only** |

**Aptos Display carries all text and every number.** Tabular figures, a plain
lining zero, and the tightest of the Aptos cuts — marginally *narrower* than
Aptos regular because its comma is 10.0 units against Aptos's 11.0.

It is a display cut, so its tracking is tuned for large sizes. Checked at 10pt
against Aptos regular it stays clean and the digit columns align exactly. The
other two cuts belong to styles, not to taste: Boardroom sets Aptos, Ledger
sets Aptos Narrow (§9). Change the style, never the face alone.

**Aptos Mono carries instrument labels only** — letters, not digits. It is the
widest face measured and has a slashed zero, and neither matters for short
uppercase labels. It is the designed sibling of the Aptos cuts, so it pairs properly;
Consolas against Aptos Display would be a family clash (XL15 catches it).

Do not use **Inter** in Excel: its figures are proportional (the `1` is 38%
narrower than the widest digit), so it cannot hold a numeric column. Inter
remains the TAR-OS *screen* face — see `tars-design`.

### Aptos is a cloud font — check the recipient

Aptos does not live in `C:\Windows\Fonts`. Microsoft 365 delivers it to
`%LOCALAPPDATA%/Microsoft/FontCache/4/CloudFonts/`, which is why it is
invisible to the system font list and to most tooling while working correctly
in Excel.

It resolves on any Microsoft 365 or Office 2024 machine. It **substitutes
silently** on Office 2019/2021 perpetual, LibreOffice, and Google Sheets —
the exact failure this contract exists to prevent. So:

| Recipient | Pair |
|---|---|
| Microsoft 365 / Office 2024 (default) | **the style's pair (§9)** |
| Known pre-2024 Office, or unknown and high-stakes | **Calibri + Consolas** |

Aptos Display, Aptos and Aptos Narrow are separate **families** to Excel, not
styles of one font — so they cannot be mixed inside a workbook any more than
Aptos and Consolas can. Write the face name exactly as Excel lists it:
`Aptos Display`.

Pick one pair and stay inside it. `excel_lint.py` XL15 enforces that, but it
**cannot** verify the font exists on the recipient's machine — that is a
judgement call about the audience, recorded in
`Cowork/clients/<X>/MEMORY.md` when known.

The role table below is the Instrument style. §9 swaps the face and sizes per
style; the roles, weights and colors stay.

| Role | Face | Size | Weight | Color |
|---|---|---|---|---|
| Title | Aptos Display | 14pt | bold | `ink` |
| Subtitle (period · units · scenario) | Aptos Display | 10pt | regular | `ink-2` |
| Section label (instrument label) | **Aptos Mono** | 9pt | bold | `ink-3` |
| Column header | Aptos Display | 10pt | bold | `ink` |
| Row label | Aptos Display | 10pt | regular | `ink` |
| **Every number, date, count** | **Aptos Display** | 10pt | regular | `ink` |
| KPI readout value | Aptos Display | 16pt | bold | `ink` |
| Footnote / source | Aptos Display | 9pt | italic | `ink-3` |

- Exactly **two faces** per workbook, both from one pair. Nothing else.
- At most **four sizes** per workbook: the style's scale (§9). Chart titles
  use the body size in bold, not a size of their own.
- Section labels are **mono UPPERCASE**. TARS widens them
  (`--tars-tracking-label:0.12em`); Excel has no letter-spacing, so that part
  is dropped rather than faked.
- Everything else is **sentence case**. No Title Case headers.
- Text left, numbers right. Never center body content. The one exception is
  the Instrument status badge, which fills its whole cell (§4).
- Headers may wrap. Never shrink-to-fit, never rotate unless a matrix needs it.
- A KPI value is marked as a readout by **size, weight and its tile** —
  not by being mono. That is enough, and it keeps the slashed zero off the
  number the reader looks at hardest.

## 2. Color

TARS rules that carry over unchanged: never pure black, tint every neutral
toward the accent hue, one accent, semantic colors reserved for meaning, flat
surfaces, no decorative gradients.

Every style uses this one palette. A style changes structure and type, never
color. Only a §10 brand override changes color, and only `accent`,
`accent-fill` and `rule`. Surfaces, text and borders always come from this
palette.

| Token | Hex | Derived from | Use |
|---|---|---|---|
| `ink` | `#292B36` | TARS gunmetal h228 | primary text (never `#000000`) |
| `ink-2` | `#515567` | same ramp | subtitles, units, secondary |
| `ink-3` | `#63677E` | same ramp | section labels, footnotes, source lines |
| `hairline` | `#D5D7DF` | `--tars-border` | separators, header/total rules |
| `band` | `#F5F5F7` | `--tars-surface-raised` | header band, zebra, card fill |
| `accent` | `#202B8A` | TARS indigo h234 | chart hero series, gauge, active tab |
| `accent-fill` | `#E8EAFA` | `--tars-accent-soft` | KPI tile fill, selected column |
| `rule` | `#202B8A` (= `accent`) | — | table header rule; a §10 override may set it apart from `accent` |
| `positive` | `#1C593E` | `--color-green` | favorable variance only |
| `negative` | `#CC2432` | `--color-red` | unfavorable variance only |
| `warning` | `#8F5F17` | `--color-orange` | caution only |
| `positive-tint` | `#E9F7F0` | `positive` hue, S45 L94 | ground of a favorable status badge |
| `negative-tint` | `#F7E9EA` | `negative` hue, S45 L94 | ground of an unfavorable status badge |
| `warning-tint` | `#F7F1E9` | `warning` hue, S45 L94 | ground of a caution status badge |
| `input` | `#1D59A3` | `--color-blue` | text of an input cell (§4) |
| `input-tint` | `#D6E4F5` | `input` hue, S60 L90 | ground of an input cell (§4) |

- The tightest verified pairs are `negative` on `accent-fill` at 4.55:1,
  `negative` on `negative-tint` at 4.60:1 and `ink-3` on `accent-fill` at
  4.66:1. Recheck all three after any token change.
- `input` on `input-tint` is 5.41:1. The dashed `ink-3` input box is 4.31:1
  on `input-tint`, above the 3:1 a border needs.
- Canvas is white. No page-wide fills. TARS layers dark surfaces; on paper the
  equivalent of a raised surface is `band` plus a `hairline` edge, not a shadow.
- Semantic colors mark **meaning**, never decoration. Red is "unfavorable",
  not "the expense section".
- Favorability, not sign: cost under budget is `positive` even though the
  variance is negative.
- At most **6 distinct fills** per workbook. Instrument's set (`band`,
  `accent-fill`, the three status tints, `input-tint`) uses all six.
- No gradient fills anywhere. TARS bans decorative gradients; in Excel that
  also rules out **data bars** (§4 Segmented gauge).

## 3. Number formats

Every numeric cell carries an explicit format. `General` on a number is a defect.

| Content | Format string |
|---|---|
| Money (body) | `#,##0;(#,##0)` |
| Money, zero as dash | `#,##0;(#,##0);"-"` |
| Money with symbol (first row of a block only) | `$#,##0;($#,##0)` |
| Percent | `0.0%;(0.0%)` |
| Multiple / ratio | `0.0x` |
| Period column header | `mmm-yy` |
| Full date | `yyyy-mm-dd` |

- Negatives in parentheses, never a bare minus in a financial column. This is
  the non-color channel that keeps variance readable in grayscale and to
  red-green colorblind readers. **Never** signal favorability by color alone.
- Units stated once in the subtitle (`USD thousands · FY26 Budget v3`), never
  per cell or per header.
- Uniform precision per column. Mixed decimals down a column is a defect.

## 4. Components

The TARS component set, translated. Each entry names its design-system source.
Build these; do not invent a parallel set per report.

### Section label — `--tars-tracking-label` motif
Mono, 9pt, bold, `ink-3`, UPPERCASE. One blank row above, none below. Replaces
a heavier heading; the report gets its hierarchy from these plus whitespace.

### KPI readout — `obsidian/StatusReadout` + `display/Card`
The TARS instrument-bar motif as a tile block:
- label row: **Aptos Mono** 9pt bold `ink-3` uppercase (an instrument label)
  that names the metric and its direction, e.g. `OPEX · UNDER`, with the
  comparison stated once in the section label (`HEADLINE · VS BUDGET`). Build
  it with a formula on the variance so it flips when the numbers do. Cost
  lines say under or over; revenue and profit lines say above or below
- value row: sans 16pt bold `ink`, the hero included. The hero is marked by
  its tile and its `rule` border, never by color, so no brand override can
  lighten the number the reader looks at hardest
- delta row: sans 10pt, the size of the variance with no sign
  (`0.0%`, or `0.0" pts"` for a margin), in `positive` or `negative` by
  favorability, set by conditional formatting on the label's own test. A leading `+` on a cost line reads as spend growth, so the
  direction lives in the label, never in the sign
- ground: `accent-fill` for the hero tile, `band` for the rest; `hairline` box.
  The hero tile also takes a medium `rule` top border, its cue that
  survives grayscale print, where `accent-fill` and `band` merge. It is
  drawn in `rule`, not `accent`, so no brand override can lighten it
  (Instrument; §9 gives the other styles' KPI treatment)
- 3 or 4 tiles in a row, never more
- each tile spans whole columns. Size the label column at exactly two data
  columns wide, so four tiles land on `B`, `C:D`, `E:F` and `G:H` and the table
  below keeps its own columns
- tiles abut, separated only by their `hairline` boxes. Never insert spacer
  columns for gaps: they would split the table underneath
- value and delta sit in separate cells. A value and delta in one cell is
  rich text, which turns the number into text that no formula can read
- the delta must fit its own cell. Excel never lets a number spill into the
  next cell and prints `####` instead. Wording such as "under budget" belongs
  in the label, never inside the delta's number format
- a readout tile is not a column, so its label, value and delta align left.
  Readouts stacked as property rows (Ledger) are a column, so their value
  and delta align right

### Segmented gauge — `display/ProgressGauge`
TARS is explicit: **segmented, never a smooth fill.** Excel's data bars are a
smooth gradient fill, so they are banned here.

Two forms. Choose by what shares the gauge's columns.

**Single-cell form**: the default on any sheet that also holds a table. One
cell, set in the pair's mono face in `accent`:
`=REPT("■",reached)&REPT("□",total-reached)`, with `reached` read from a
named period cell (e.g. `MonthsElapsed`), never typed. Filled and hollow squares stay
apart in grayscale by shape, so the gauge needs one color, not rich text. Aptos
Mono and Consolas both carry U+25A0 and U+25A1. Aptos Display, Aptos and Aptos
Narrow lack U+25A0, so never set the gauge in the sans.

**Narrow-cell form**: only on a sheet where no table uses the gauge's
columns, such as a dedicated tracker. **One narrow cell per segment** (5 for a
headline, 12 for subtask detail), each filled `accent` when reached and
`hairline` when not, column width ~1.6, `hairline` box around the run. Narrow
columns inside a table's span break column selection and copy.

### Status badge — `display/Badge`
Squared pill, never rounded (Excel cannot round a cell — TARS's 3/4/6/10px
radius scale has no analogue and is dropped, not approximated). The badge is
the whole cell: fill, a `hairline` left, right and bottom edge, and centered
text. Excel cannot inset a chip inside a cell. The top edge belongs to the
row above (XL17), so a badge never redraws a neighbour's line. Sans 9pt bold, status color text on its own tint
(`positive-tint`, `negative-tint`, `warning-tint`), so the ground signals the
status before the word is read. The tints are near-identical in grayscale, so
the word still carries the meaning on paper. Sentence case.

The status words are favorability, not direction, so they read the same on
revenue and cost lines: **Ahead** (favorable by 3% or more), **On track**
(favorable under 3%), **Watch** (unfavorable under 3%), **Behind**
(unfavorable by 3% or more). Ahead and On track use `positive`, Watch
`warning`, Behind `negative`. The threshold is one named cell, `StatusBand`
(default 3%), on the inputs tab. The status formulas, their conditional
formats and the footnote text all read it, so moving it is one edit; a client
may set it, and the footnote states all four definitions either way. Line items carry a status;
subtotals do not, and the footnote says so.

The status word is a formula on the favorability %, and its color and tint
come from conditional formatting on the same value, so the badge follows the
number. The same holds for every favorability color in a report: KPI deltas,
Variance and Var % keep an `ink` base font and take `positive` or `negative`
from conditional formatting. A static red or green goes stale the moment a
number changes.

The whole-cell badge is centered. A status set as text (Boardroom's marker,
Ledger's bold word) is a column of words, so it aligns left with indent 1. Strip the emoji from vault `Status` enum values. TARS
bans emoji in the interface and that holds here.

### Property row — `obsidian/PropertyRow`
Key/value pair for cover sheets and assumption blocks: label sans 10pt
`ink-2` left, value sans 10pt `ink` right, `hairline` separator between rows.
No fill. Values here are numbers and dates, so they follow the numeral rule.
Ledger uses property rows for its KPI block: value and delta right, and the
hero is the only bold value, a weight cue that survives grayscale print.

### Input cell — hardcoded values
A value someone typed: an assumption, an actual, a budget. Formulas never
carry this treatment, so an input reads apart from a formula on screen by
fill, color and outline, and in print by its outline.
- `input` text on an `input-tint` fill, inside a box of Excel's `dashed`
  style in `ink-3` on all four sides. The treatment is the same in every
  style.
- Neighbouring inputs declare their shared side identically, so a run of
  inputs reads as one block and XL17 passes.
- A header rule or a total rule keeps its edge and the box opens there: the
  first line under a header, and Ledger's line above a subtotal. Elsewhere
  the dash replaces the row's `hairline`.
- The footnote key reads "Tinted, boxed figures are hardcoded inputs."
- XL12 does not count an input box (three or more dashed sides) as a
  border grid.

### Table — `obsidian/TaskRow`
- header row: sans bold `ink`, one header row, styled by the style's header
  treatment (§9). Instrument: `band` fill and a `rule` medium bottom border
- rows: `hairline` horizontal separators only. **No vertical borders**, except
  the input box (§4 Input cell). The
  full border grid is the single biggest Excel slop tell and is exactly the
  boxed look TARS avoids with seams
- zebra (`band`) only past ~12 rows; below that whitespace does the work
- every table cell is vertically centred, so badges and numbers share a
  baseline in tall rows
- total row: `hairline` top + bold (Ledger: thin `ink`). Grand total: double
  top border (Ledger also closes it with a medium `ink` rule)
- declare each shared edge on one cell only. Excel draws one line per edge,
  so a total rule set on both neighbours renders whichever wins (XL17)
- freeze panes below the header on anything past 30 rows

### Card / block — `display/Card`
`band` fill, `hairline` box, no shadow, no rounding. TARS's raised surfaces
become flat tone-plus-edge on paper.

### No analogue — dropped, not faked
Radius scale (Excel cells are rectangles) · motion 90-220ms · hover/focus/
active states · Lucide icons at stroke 1.9 (and emoji are **not** a substitute).

## 5. Sheet layout

- **Gridlines off** on every delivered sheet. Structure comes from the layout.
- Column A is a **margin**: width 2-3, always empty. Content starts at B.
- Header block: row 1 title · row 2 subtitle · row 3 spacer. Data from row 4.
- Excel measures column widths in digits of the workbook's first font record.
  openpyxl leaves that record Calibri 11 whatever the Normal style says, so
  every width in this contract is in Calibri 11 digits.
- Row height follows the largest font in the row: x 1.4 up to 12pt, x 1.25
  up to 16pt, x 1.1 above, rounded up to the next 0.75pt (one pixel at 100%
  zoom). Table and KPI rows never go below the style's body row height (§9);
  footnote rows follow the ratio alone, so 9pt notes are not double-spaced.
  Large type gets
  proportionally tighter rows, so a KPI value does not float in its tile.
- **No merged cells.** Use center-across-selection. Merges break sorting,
  copying, and every downstream script.
- Consistent data column widths within a block; size to the widest realistic
  value, not to the header.

## 6. Charts

- Flat. No 3D, shadows, bevels, gradients, or plot-area borders.
- Hero series `accent`; context series `ink-3`. Semantic colors only for
  semantic series.
- Horizontal `hairline` gridlines only; axis text sans 9pt `ink-2`.
- Legend off for a single series. Label the last point directly instead of
  forcing a legend lookup when tracking one or two series over time.
- Title sentence case at the body size in bold, or omitted when the sheet
  title already says it.

## 7. Workbook structure and finish

- Tab order tells the reading story: summary → report tabs → data → reference.
- Tab names are short nouns (`Summary`, `P&L`, `Variance`, `Data`), never
  `Sheet1`. Tab colors mark semantic groups only, max 3 distinct.
- Hide scaffolding sheets; never deliver a visible junk tab.
- Park every sheet at **A1, zoom 100%**, summary tab active on save.
- Set print areas on report tabs; landscape, fit to one page wide (never one
  page tall: a long sheet would shrink to fit), repeat header row, 0.5in side
  margins. After any shrink every printed line, numbers, labels and footnotes
  alike, must print at 7pt or more (XL18). A sheet that prints below 100% sets
  its section labels and footnotes at body size. Fix a failure by narrowing
  columns, dropping columns or moving to larger paper, never by letting the
  type shrink.
- Terse factual copy. No emoji, no exclamation marks, no praise — the TARS
  voice rule, unchanged.
- Always `.xlsx`, never `.xls` — gotcha `xlsx-not-xls` (breaks the Datarails
  add-in).

## 8. Anti-patterns (lint rules)

`excel_lint.py` detects these deterministically. Exit 2 = findings exist.
Fix true findings before recording an exception; never waive a whole workbook.

| Rule | Anti-pattern |
|---|---|
| XL1 | Gridlines visible on a delivered sheet |
| XL2 | Merged cells |
| XL3 | Default tab names (`Sheet1`, ...) |
| XL4 | Font sprawl: >2 faces or >4 sizes |
| XL5 | Pure black (`#000000`) declared as a font color |
| XL6 | Fill sprawl: >6 distinct solid fills |
| XL7 | Numeric cell left on `General` format |
| XL8 | Scrolling table (>30 rows) without freeze panes |
| XL9 | Sheet not parked at A1 / zoom != 100% |
| XL10 | Tab-color rainbow: >3 distinct tab colors |
| XL11 | Formatting bloat: styled range vastly exceeds content — heuristic |
| XL12 | Border grid: large share of populated cells boxed all four sides; dashed input boxes (§4) are exempt — heuristic |
| XL13 | Gradient fill (TARS bans decorative gradients) |
| XL14 | Data bar or color-scale conditional format — use a segmented gauge (§4) |
| XL15 | Face outside one approved pair, or faces spanning two families |
| XL16 | Numeric cell in a proportional-figure face — the column cannot align |
| XL17 | A shared cell edge declared on both neighbours with different borders |
| XL18 | Any printed line below 7pt once fit-to-width, fit-to-height or a fixed scale shrinks the page |

XL11 and XL12 are labeled heuristics in their own output. A raw data-dump tab
may legitimately waive XL11 with a stated reason. XL16 is not a heuristic — a
proportional-figure column is always misaligned. XL18 estimates the printed
size from column widths and page setup. Calibrated against Excel 16 PDF
export, it reads up to 0.35pt low and never high, so a pass is safe.
`not_run` is not `pass`; `waived` is not `pass`.

## 9. Styles

A style sets the face pair, type scale, row height, column widths and three
treatments: the header row, the KPI block and the status column.
Everything else in this contract is the same in every style. Choose the style
in the Shape step from the audience. A client may pin one with
`Excel style: <name>` in `Cowork/clients/<X>/MEMORY.md`. The default is
Instrument.

| | Instrument (default) | Boardroom | Ledger |
|---|---|---|---|
| Use for | internal and client reports | board packs, executive one-pagers | close packs, models, many period columns, black-and-white print |
| Pair | Aptos Display + Aptos Mono | Aptos + Aptos Mono | Aptos Narrow + Aptos Mono |
| Title · body · label · KPI (pt) | 14 · 10 · 9 · 16 | 20 · 11 · 9 · 22 | 12 · 9 · 9 · 12 |
| Body row height | 15pt | 18pt | 12.75pt |
| Data column width (Calibri 11 digits) | 14 | 15, so the summary fits Letter landscape at 100% | 8, sized to the widest value |
| Label column | two data columns, so tiles land on the table's edges | two data columns | sized to the longest line label (no tiles to align) |
| Summary column budget at 100% | label + 6 data columns | label + 6 data columns | label + 12 data columns |
| Period sheet: data · label width | 9 · 21 | 10 · 24 | 8 · 20 (labels and footnotes at body size on every period sheet) |
| Header row and rules | `band` fill, `rule` medium bottom border; `hairline` subtotal rules | `ink` fill, white bold text; `hairline` subtotal rules | no fill, `ink` medium top and thin bottom border; thin `ink` rule above subtotals, double above the grand total and a medium `ink` rule closing it |
| KPI block | tiles: hero on `accent-fill` with a medium `rule` top border, rest on `band`, `hairline` box, text at indent 1, a 6pt spacer row above | no fill: medium `rule` top border on the hero, `hairline` top border on the rest, a 6pt spacer row above, labels hung from the rule | property rows: label, then value and delta right-aligned, hero the only bold value |
| Status column | badge on its status tint, centered (§4) | `▪` marker and word in the status color, left at indent 1; the cell holds the bare word and the marker comes from the number format `"▪ "@` | bold word in the status color, left at indent 1 |
| Fills besides zebra `band` | `band`, `accent-fill`, the three status tints, `input-tint` | `ink`, `input-tint` | `input-tint` |

- The fallback pair (Calibri + Consolas, §1) replaces any style's pair for a
  pre-2024 Office recipient. Sizes and treatments stay.
- Each style stays inside one approved pair (XL15) and four sizes (XL4).
- The hero KPI value is `ink` in every style. Its cue survives grayscale and
  any override: a medium `rule` top border (Instrument, Boardroom) or the
  only bold value (Ledger).
- Measured printed sizes (Excel 16 PDF export, Letter landscape, 0.5in side
  margins): the Instrument summary prints at 100% (10pt body), Boardroom at
  100% (11pt body, 22pt KPI), Ledger at 100% (9pt body). A column beyond the
  summary budget shrinks the page: one more Boardroom column takes 11pt to
  about 10pt. Past the budget, move the extra columns to a detail tab.
- Boardroom's `▪` (U+25AA) is in every Aptos cut, so it sits in the sans.
  Marker and word survive print without a fill.
- Ledger stays legible in black and white because favorability is carried by
  parentheses and status text, which every style already requires (§3).
- Every style can carry period sheets: a period tab uses the style's period
  widths, keeps the workbook's one face pair, sets its labels and footnotes at
  body size and passes XL18. Measured on the specimen workbooks, which hold a
  Summary and a 12-month tab together: the 12-month tab (16 data columns), fit
  to one Letter landscape page wide, prints every line at 7.56pt or more in
  all three styles. Ledger stays the choice for a workbook that is mostly
  period sheets: its 9pt body suits a dense close pack.
- **A period sheet holds at most 16 data columns on Letter landscape**, in
  every style, at the period widths above. Measured, Excel 16 PDF export
  against the XL18 estimate:

  | Data columns | Instrument | Boardroom | Ledger |
  |---|---|---|---|
  | 16: printed · XL18 estimate | 7.56 · 7.33pt | 7.56 · 7.28pt | 7.56 · 7.29pt |
  | 17: printed · XL18 estimate | 7.20 · 6.95pt | 7.08 · 6.91pt | 7.20 · 6.92pt |

  A 17th column still prints above 7pt, but the estimate reads up to 0.35pt
  low and XL18 fails it. The limit is the lint's, not legibility's. A sheet
  that needs more columns takes one of four ways out:
  1. drop a column, or move it to a second sheet (Var % is the usual one);
  2. print on larger paper: Legal or Tabloid landscape;
  3. narrow the data columns below the period width, while the widest value
     still fits;
  4. tighten the XL18 estimate, a lint change with its own tests.

## 10. Client brand override

A client may change three tokens and nothing else. Brand color carries the
accent and its tint. Neutral surfaces, text and borders stay on the palette,
so every client's report reads as the same system. Record the override in
`Cowork/clients/<X>/MEMORY.md`:

```
Excel brand: accent #4646CE · rule #0C142B
```

Every field is optional, and each omitted field keeps its default. A legacy
`Excel accent: #RRGGBB` line is an override of `accent` alone.

- **`accent-fill` not given** — derive it: the accent's hue at HSL saturation
  70% and lightness 95%. That rule reproduces the default `#E8EAFA` from
  `#202B8A` to within one step.
- **`rule` not given** — it follows `accent`.
- Instrument draws all three tokens. Boardroom draws `accent` and `rule` (the
  hero border). Ledger draws only `accent`.

Each token must pass its check, measured with WCAG contrast. A token that
fails keeps its default; tell the user which one and why.

| Token | Must hold |
|---|---|
| `accent` | >= 4.5:1 on white and on `accent-fill`. It colors gauge glyphs and a chart's hero series, never the hero KPI value, which stays `ink` |
| `accent-fill` | `ink-3`, `positive`, `negative` and `warning` each >= 4.5:1 on it |
| `rule` | >= 3:1 on white, so the header edge survives grayscale print |

Never overridden: `band`, the `ink` ramp, `hairline`, the semantic colors and
their tints, `input` and `input-tint`, faces and sizes. A brand typeface cannot ship inside an `.xlsx`. It substitutes silently
on any machine without it, and most brand faces lack tabular figures anyway.

Worked example: Datarails. The brand's only typeface is Poppins, so the faces
stay Aptos. Brand pink is not used for `negative`: semantic colors never
carry brand. The brand indigo `#4646CE` passes as is: 6.94:1 on white and
5.78:1 on its derived fill.

| Token | Value | Tightest check |
|---|---|---|
| `accent` | `#4646CE` | 5.78:1 on `accent-fill` |
| `accent-fill` | `#E9E9FB` (derived) | `negative` 4.53:1 |
| `rule` | `#0C142B` | 18.25:1 on white |
