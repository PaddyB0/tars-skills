# Excel report design contract

The single visual authority for every `.xlsx` report generated in this OS.

Two sources feed it. The **TARS design system** (`.obsidian/design-system/`)
supplies identity — the gunmetal neutral ramp, the indigo accent, mono
instrument labels, flat surfaces, hairline seams, segmented gauges. The concepts in [pbakaus/impeccable](https://github.com/pbakaus/impeccable)
supply method — tokens documented once, deterministic anti-pattern detection,
restraint over decoration. `excel_lint.py` enforces the testable subset; this
file is the full contract.

Client brand override: a client may declare `Excel accent: #RRGGBB` in
`Cowork/clients/<X>/MEMORY.md`. That replaces the accent token only.
Everything else here is invariant.

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
keeps the indigo hue 234. Every text token clears WCAG AA (>= 4.5:1 on white).

One further constraint TARS never faces: **these reports get printed in black
and white.** Favorable and unfavorable must stay tellable apart with the color
gone, so `positive` and `negative` are separated in luminance as well as hue
(1.51:1 grayscale, verified). Color is never the only channel anyway — see §3.

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
| Aptos Narrow | yes (20.0) | 46.9pt | plain | Excel's M365 default body face |
| **Aptos Display** | **yes (21.0)** | **47.2pt** | **plain** | **the body and numeral face** |
| Aptos | yes (21.0) | 48.7pt | plain | approved alternate |
| Arial | yes | 50.5pt | plain | — |
| Inter | **no (16.0-26.0)** | 53.8pt | plain | cannot align a column |
| Consolas | yes | 60.5pt | slashed | fallback mono |
| **Aptos Mono** | yes (24.0) | 66.0pt | slashed | **instrument labels only** |

**Aptos Display carries all text and every number.** Tabular figures, a plain
lining zero, and the tightest of the Aptos cuts — marginally *narrower* than
Aptos regular because its comma is 10.0 units against Aptos's 11.0.

It is a display cut, so its tracking is tuned for large sizes. Checked at 10pt
against Aptos regular it stays clean and the digit columns align exactly; the
difference at body size is slight. If a report ever reads too tight — very
dense tables, or a client printing at reduced scale — **Aptos** regular is the
approved alternate and needs no other change.

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
| Microsoft 365 / Office 2024 (default) | **Aptos Display + Aptos Mono** |
| Body size reads too tight | **Aptos + Aptos Mono** |
| Many period columns to fit | **Aptos Narrow + Aptos Mono** |
| Known pre-2024 Office, or unknown and high-stakes | **Calibri + Consolas** |

Aptos Display, Aptos and Aptos Narrow are separate **families** to Excel, not
styles of one font — so they cannot be mixed inside a workbook any more than
Aptos and Consolas can. Write the face name exactly as Excel lists it:
`Aptos Display`.

Pick one pair and stay inside it. `excel_lint.py` XL15 enforces that, but it
**cannot** verify the font exists on the recipient's machine — that is a
judgement call about the audience, recorded in
`Cowork/clients/<X>/MEMORY.md` when known.

| Role | Face | Size | Weight | Color |
|---|---|---|---|---|
| Title | Aptos Display | 14pt | bold | `ink` |
| Subtitle (period · units · scenario) | Aptos Display | 10pt | regular | `ink-2` |
| Section label (instrument label) | **Aptos Mono** | 9pt | bold | `ink-3` |
| Column header | Aptos Display | 10pt | bold | `ink` |
| Row label | Aptos Display | 10pt | regular | `ink` |
| **Every number, date, count** | **Aptos Display** | 10pt | regular | `ink` |
| KPI readout value | Aptos Display | 16pt | bold | `ink` or `accent` |
| Footnote / source | Aptos Display | 9pt | italic | `ink-3` |

- Exactly **two faces** per workbook, both from one pair. Nothing else.
- At most **five sizes** (9, 10, 11, 14, 16).
- Section labels are **mono UPPERCASE**. TARS widens them
  (`--tars-tracking-label:0.12em`); Excel has no letter-spacing, so that part
  is dropped rather than faked.
- Everything else is **sentence case**. No Title Case headers.
- Text left, numbers right. Never center body content.
- Headers may wrap. Never shrink-to-fit, never rotate unless a matrix needs it.
- A KPI value is marked as a readout by **size, weight, color and its tile** —
  not by being mono. That is enough, and it keeps the slashed zero off the
  number the reader looks at hardest.

## 2. Color

TARS rules that carry over unchanged: never pure black, tint every neutral
toward the accent hue, one accent, semantic colors reserved for meaning, flat
surfaces, no decorative gradients.

| Token | Hex | Derived from | Use |
|---|---|---|---|
| `ink` | `#292B36` | TARS gunmetal h228 | primary text (never `#000000`) |
| `ink-2` | `#5A5F72` | same ramp | subtitles, units, secondary |
| `ink-3` | `#6B7088` | same ramp | section labels, footnotes, source lines |
| `hairline` | `#D5D7DF` | `--tars-border` | separators, header/total rules |
| `band` | `#F5F5F7` | `--tars-surface-raised` | header band, zebra, card fill |
| `accent` | `#202B8A` | TARS indigo h234 | header band rule, hero series, KPI value, gauge fill |
| `accent-fill` | `#E8EAFA` | `--tars-accent-soft` | KPI tile fill, selected column, badge ground |
| `positive` | `#1C593E` | `--color-green` | favorable variance only |
| `negative` | `#CC2432` | `--color-red` | unfavorable variance only |
| `warning` | `#8F5F17` | `--color-orange` | caution only |
| `input` | `#1D59A3` | `--color-blue` | hardcoded input cells the client edits |

- Canvas is white. No page-wide fills. TARS layers dark surfaces; on paper the
  equivalent of a raised surface is `band` plus a `hairline` edge, not a shadow.
- Semantic colors mark **meaning**, never decoration. Red is "unfavorable",
  not "the expense section".
- Favorability, not sign: cost under budget is `positive` even though the
  variance is negative.
- At most **6 distinct fills** per workbook.
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
- value row: sans 16pt bold, `ink` (or `accent` for the hero metric)
- delta row: sans 10pt, `positive`/`negative`, always with a signed or
  parenthesized format
- ground: `accent-fill` for the hero tile, `band` for the rest; `hairline` box
- laid out across 3 or 4 columns, never more than 4 in a row

### Segmented gauge — `display/ProgressGauge`
TARS is explicit: **segmented, never a smooth fill.** Excel's data bars are a
smooth gradient fill, so they are banned here.

Canonical form — **one narrow cell per segment** (5 for a headline, 12 for
subtask detail), each filled `accent` when reached and `hairline` when not,
column width ~1.6, `hairline` box around the run. Fully portable, no glyph
dependency.

Single-cell fallback where only one cell is available: a `REPT` formula of
block glyphs in `accent`, set in Aptos Mono so the segments are even width.
Confirm the glyphs render in the delivery font before using it.

### Status badge — `display/Badge`
Squared pill, never rounded (Excel cannot round a cell — TARS's 3/4/6/10px
radius scale has no analogue and is dropped, not approximated). Centered,
sans 9pt bold, status color text on `accent-fill` or the status tint,
`hairline` box, sentence case. Strip the emoji from vault `Status` enum values
— TARS bans emoji in the interface and that holds here.

### Property row — `obsidian/PropertyRow`
Key/value pair for cover sheets and assumption blocks: label sans 10pt
`ink-2` left, value sans 10pt `ink` right, `hairline` separator between rows.
No fill. Values here are numbers and dates, so they follow the numeral rule.

### Table — `obsidian/TaskRow`
- header band: sans 10pt bold `ink` on `band`, `accent` medium bottom border,
  one header row
- rows: `hairline` horizontal separators only. **No vertical borders.** The
  full border grid is the single biggest Excel slop tell and is exactly the
  boxed look TARS avoids with seams
- zebra (`band`) only past ~12 rows; below that whitespace does the work
- total row: `hairline` top + bold. Grand total: double top border
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
- Title sentence case 11pt, or omitted when the sheet title already says it.

## 7. Workbook structure and finish

- Tab order tells the reading story: summary → report tabs → data → reference.
- Tab names are short nouns (`Summary`, `P&L`, `Variance`, `Data`), never
  `Sheet1`. Tab colors mark semantic groups only, max 3 distinct.
- Hide scaffolding sheets; never deliver a visible junk tab.
- Park every sheet at **A1, zoom 100%**, summary tab active on save.
- Set print areas on report tabs; landscape, fit-to-width, repeat header row.
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
| XL4 | Font sprawl: >2 faces or >5 sizes |
| XL5 | Pure black (`#000000`) declared as a font color |
| XL6 | Fill sprawl: >6 distinct solid fills |
| XL7 | Numeric cell left on `General` format |
| XL8 | Scrolling table (>30 rows) without freeze panes |
| XL9 | Sheet not parked at A1 / zoom != 100% |
| XL10 | Tab-color rainbow: >3 distinct tab colors |
| XL11 | Formatting bloat: styled range vastly exceeds content — heuristic |
| XL12 | Border grid: large share of populated cells boxed all four sides — heuristic |
| XL13 | Gradient fill (TARS bans decorative gradients) |
| XL14 | Data bar or color-scale conditional format — use a segmented gauge (§4) |
| XL15 | Face outside one approved pair, or faces spanning two families |
| XL16 | Numeric cell in a proportional-figure face — the column cannot align |

XL11 and XL12 are labeled heuristics in their own output. A raw data-dump tab
may legitimately waive XL11 with a stated reason. XL16 is not a heuristic — a
proportional-figure column is always misaligned.
`not_run` is not `pass`; `waived` is not `pass`.
