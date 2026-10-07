#!/usr/bin/env python3
"""Deterministic design lint for delivered .xlsx reports.

Enforces the testable subset of the excel-design contract
(references/DESIGN.md). Rules XL1-XL18. Exit codes mirror the Impeccable
runner: 0 clean, 2 findings exist, 1 the file could not be checked.

XL11 and XL12 are heuristics and say so in their own output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, range_boundaries

DEFAULT_TAB_NAME = re.compile(r"^Sheet\d*$", re.IGNORECASE)
PURE_BLACK = "FF000000"
MAX_FACES = 2
MAX_SIZES = 4
# The type contract is one sans + its mono sibling (references/DESIGN.md §1).
# Excel has no fallback stack, so a workbook must stay inside ONE pair - mixing
# Aptos with Consolas is a family clash, not a valid two-face budget.
# Aptos ships with Microsoft 365 as a cloud font; the Calibri pair is the
# documented fallback for a client on pre-2024 Office.
APPROVED_PAIRS = (
    frozenset({"Aptos Display", "Aptos Mono"}),   # the default pair
    frozenset({"Aptos", "Aptos Mono"}),
    frozenset({"Aptos Narrow", "Aptos Mono"}),
    frozenset({"Calibri", "Consolas"}),
)
SANS_FACES = {"Aptos Display", "Aptos", "Aptos Narrow", "Calibri"}
MONO_FACES = {"Aptos Mono", "Consolas"}
APPROVED_FACES = SANS_FACES | MONO_FACES
# Numerals need TABULAR (fixed-width) figures or a column cannot align. Measured
# with PIL at size 40: every digit identical width = tabular. Inter is 16.0-26.0
# and Bahnschrift 13.0-23.0, so neither can carry a numeric column.
PROPORTIONAL_FIGURE_FACES = {"Inter", "Bahnschrift"}
SMOOTH_FILL_CF_TYPES = {"dataBar", "colorScale"}
MAX_FILLS = 6
MAX_TAB_COLORS = 3
FREEZE_ROW_THRESHOLD = 30
BLOAT_MAX_ROW = 20000
BLOAT_MAX_COL = 150
BOXED_MIN_CELLS = 30
BOXED_MIN_SHARE = 0.5
MAX_EXAMPLES = 5


def _finding(rule: str, sheet: str | None, detail: str) -> dict:
    return {"rule": rule, "sheet": sheet, "detail": detail}


def _visible_sheets(wb):
    return [ws for ws in wb.worksheets if ws.sheet_state == "visible"]


def _iter_value_cells(ws):
    for row in ws.iter_rows():
        for cell in row:
            if cell.value is not None:
                yield cell


def _fmt_examples(addresses: list[str]) -> str:
    shown = ", ".join(addresses[:MAX_EXAMPLES])
    extra = len(addresses) - MAX_EXAMPLES
    return shown + (f" (+{extra} more)" if extra > 0 else "")


def _check_gridlines(ws) -> list[dict]:  # XL1
    # After a load round-trip openpyxl reports the absent attribute as None,
    # which Excel renders as gridlines shown. Only an explicit False is clean.
    if ws.sheet_view.showGridLines is not False:
        return [_finding("XL1", ws.title, "gridlines are visible; turn them off")]
    return []


def _check_merged(ws) -> list[dict]:  # XL2
    ranges = [str(r) for r in ws.merged_cells.ranges]
    if ranges:
        return [
            _finding(
                "XL2",
                ws.title,
                f"{len(ranges)} merged range(s): {_fmt_examples(ranges)}; "
                "use center-across-selection",
            )
        ]
    return []


def _check_tab_names(wb) -> list[dict]:  # XL3
    bad = [ws.title for ws in wb.worksheets if DEFAULT_TAB_NAME.match(ws.title)]
    if bad:
        return [_finding("XL3", None, f"default tab name(s): {', '.join(bad)}")]
    return []


def _workbook_faces(wb) -> set[str]:
    faces: set[str] = set()
    for ws in _visible_sheets(wb):
        for cell in _iter_value_cells(ws):
            if cell.font.name:
                faces.add(cell.font.name)
    return faces


def _check_font_sprawl(wb) -> list[dict]:  # XL4
    faces = _workbook_faces(wb)
    sizes: set[float] = set()
    for ws in _visible_sheets(wb):
        for cell in _iter_value_cells(ws):
            if cell.font.size:
                sizes.add(float(cell.font.size))
    findings = []
    if len(faces) > MAX_FACES:
        findings.append(
            _finding(
                "XL4",
                None,
                f"{len(faces)} font faces ({', '.join(sorted(faces))}); "
                f"at most {MAX_FACES} - one sans + one mono",
            )
        )
    if len(sizes) > MAX_SIZES:
        listed = ", ".join(f"{s:g}" for s in sorted(sizes))
        findings.append(
            _finding("XL4", None, f"{len(sizes)} font sizes ({listed}); at most {MAX_SIZES}")
        )
    return findings


def _check_approved_faces(wb) -> list[dict]:  # XL15
    """Every face in the workbook must come from one approved pair."""
    faces = _workbook_faces(wb)
    if not faces or any(faces <= pair for pair in APPROVED_PAIRS):
        return []
    stray = sorted(faces - APPROVED_FACES)
    listed = " / ".join(
        "+".join(sorted(pair)) for pair in APPROVED_PAIRS
    )
    detail = (
        f"unapproved face(s): {', '.join(stray)}"
        if stray
        else f"faces {', '.join(sorted(faces))} span more than one family"
    )
    return [_finding("XL15", None, f"{detail}; use one pair - {listed}")]


def _check_pure_black(ws) -> list[dict]:  # XL5
    hits = [
        cell.coordinate
        for cell in _iter_value_cells(ws)
        if cell.font.color is not None
        and cell.font.color.type == "rgb"
        and cell.font.color.rgb == PURE_BLACK
    ]
    if hits:
        return [
            _finding(
                "XL5",
                ws.title,
                f"pure black #000000 declared on {len(hits)} cell(s): "
                f"{_fmt_examples(hits)}; use ink #292B36",
            )
        ]
    return []


def _check_fill_sprawl(wb) -> list[dict]:  # XL6
    fills: set[str] = set()
    for ws in _visible_sheets(wb):
        for cell in _iter_value_cells(ws):
            fill = cell.fill
            if fill is None or fill.tagname != "patternFill":
                continue  # gradientFill has no patternType; XL13 owns it
            if fill.patternType == "solid":
                color = fill.fgColor
                if color is not None and color.type == "rgb" and color.rgb:
                    rgb = str(color.rgb)
                    if rgb not in ("00000000", "FFFFFFFF"):
                        fills.add(rgb)
    if len(fills) > MAX_FILLS:
        return [
            _finding(
                "XL6",
                None,
                f"{len(fills)} distinct solid fills; at most {MAX_FILLS} "
                f"({', '.join(sorted(fills))})",
            )
        ]
    return []


def _check_general_numbers(ws) -> list[dict]:  # XL7
    hits = [
        cell.coordinate
        for cell in _iter_value_cells(ws)
        if isinstance(cell.value, (int, float))
        and not isinstance(cell.value, bool)
        and cell.number_format == "General"
    ]
    if hits:
        return [
            _finding(
                "XL7",
                ws.title,
                f"{len(hits)} numeric cell(s) on General format: {_fmt_examples(hits)}; "
                "every number carries an explicit format",
            )
        ]
    return []


def _check_freeze(ws) -> list[dict]:  # XL8
    if ws.max_row > FREEZE_ROW_THRESHOLD and not ws.freeze_panes:
        return [
            _finding(
                "XL8",
                ws.title,
                f"{ws.max_row} rows with no freeze panes; freeze below the header",
            )
        ]
    return []


def _cursor_selection(view):
    """The selection in the pane holding the cursor.

    A frozen sheet stores one selection per pane, and Excel writes the real
    cursor in the active pane's entry. On a two-axis freeze the first entry is
    topRight, whose cells start past column A, so it can never read A1. An
    absent pane attribute or activePane means topLeft.
    """
    active_pane = (view.pane.activePane if view.pane is not None else None) or "topLeft"
    for selection in view.selection:
        if (selection.pane or "topLeft") == active_pane:
            return selection
    return view.selection[0]


def _check_parked(ws) -> list[dict]:  # XL9
    findings = []
    zoom = ws.sheet_view.zoomScale
    if zoom is not None and zoom != 100:
        findings.append(_finding("XL9", ws.title, f"zoom is {zoom}%; park at 100%"))
    if ws.sheet_view.selection:
        selection = _cursor_selection(ws.sheet_view)
        active = selection.activeCell or selection.sqref
        if active is not None and str(active).split(":")[0] != "A1":
            findings.append(
                _finding("XL9", ws.title, f"cursor parked at {active}; park at A1")
            )
    return findings


def _check_tab_rainbow(wb) -> list[dict]:  # XL10
    colors = {
        str(ws.sheet_properties.tabColor.rgb)
        for ws in wb.worksheets
        if ws.sheet_properties.tabColor is not None
        and ws.sheet_properties.tabColor.type == "rgb"
    }
    if len(colors) > MAX_TAB_COLORS:
        return [
            _finding(
                "XL10",
                None,
                f"{len(colors)} distinct tab colors; at most {MAX_TAB_COLORS} semantic groups",
            )
        ]
    return []


def _check_gradient_fill(ws) -> list[dict]:  # XL13
    hits = [
        cell.coordinate
        for cell in _iter_value_cells(ws)
        if cell.fill is not None and cell.fill.tagname == "gradientFill"
    ]
    if hits:
        return [
            _finding(
                "XL13",
                ws.title,
                f"gradient fill on {len(hits)} cell(s): {_fmt_examples(hits)}; "
                "surfaces are flat tone plus hairline edge",
            )
        ]
    return []


def _check_smooth_conditional_formats(ws) -> list[dict]:  # XL14
    findings = []
    for rng in ws.conditional_formatting:
        for rule in rng.rules:
            if rule.type in SMOOTH_FILL_CF_TYPES:
                findings.append(
                    _finding(
                        "XL14",
                        ws.title,
                        f"{rule.type} conditional format on {rng.sqref}; "
                        "progress uses a segmented gauge, never a smooth fill",
                    )
                )
    return findings


def _check_proportional_figures(ws) -> list[dict]:  # XL16
    """A numeric column set in a proportional-figure face cannot align."""
    hits = [
        cell.coordinate
        for cell in _iter_value_cells(ws)
        if isinstance(cell.value, (int, float))
        and not isinstance(cell.value, bool)
        and cell.font.name in PROPORTIONAL_FIGURE_FACES
    ]
    if hits:
        return [
            _finding(
                "XL16",
                ws.title,
                f"{len(hits)} numeric cell(s) in a proportional-figure face: "
                f"{_fmt_examples(hits)}; digits vary in width so the column "
                "cannot align - use a tabular-figure face",
            )
        ]
    return []


def _check_bloat(ws) -> list[dict]:  # XL11 (heuristic)
    if ws.max_row > BLOAT_MAX_ROW or ws.max_column > BLOAT_MAX_COL:
        return [
            _finding(
                "XL11",
                ws.title,
                f"styled range spans {ws.max_row} rows x {ws.max_column} columns "
                "(heuristic: likely whole-row/column formatting); style only the content",
            )
        ]
    return []


def _has_four_borders(cell) -> bool:
    border = cell.border
    return all(
        side is not None and side.style is not None
        for side in (border.top, border.bottom, border.left, border.right)
    )


def _is_input_box(cell) -> bool:
    """DESIGN.md §4 input cell: a dashed box. One side may instead be a header or
    total rule that owns that edge, so three dashed sides are enough."""
    border = cell.border
    sides = (border.top, border.bottom, border.left, border.right)
    return sum(1 for side in sides if side is not None and side.style == "dashed") >= 3


def _check_border_grid(ws) -> list[dict]:  # XL12 (heuristic)
    populated = 0
    boxed = 0
    for cell in _iter_value_cells(ws):
        populated += 1
        if _has_four_borders(cell) and not _is_input_box(cell):
            boxed += 1
    if boxed >= BOXED_MIN_CELLS and populated and boxed / populated >= BOXED_MIN_SHARE:
        return [
            _finding(
                "XL12",
                ws.title,
                f"{boxed}/{populated} populated cells boxed on all four sides "
                "(heuristic: border grid); use hairline separators and header/total borders",
            )
        ]
    return []


# XL18: Excel sizes columns in digits of the workbook's FIRST font record (openpyxl
# leaves it Calibri 11, whatever the Normal style says). Max digit width and padding
# in px at 96 dpi, measured in Excel 16 on 2026-10-07. Calibrated against PDF export:
# the estimate reads up to 0.35pt below the printed size, and never above it.
MIN_PRINTED_PT = 7.0
DIGIT_WIDTH_PX = {
    "Aptos Display": {8: (5.33, 3.33), 9: (6.0, 4.67), 10: (6.67, 4.67), 11: (8.0, 4.67), 12: (8.67, 6.0)},
    "Aptos": {8: (6.0, 4.67), 9: (6.67, 4.67), 10: (7.33, 4.67), 11: (8.0, 4.67), 12: (8.67, 6.0)},
    "Aptos Narrow": {8: (5.33, 3.33), 9: (6.0, 4.67), 10: (6.67, 4.67), 11: (7.33, 4.67), 12: (8.0, 4.67)},
    "Calibri": {8: (5.33, 3.33), 9: (6.0, 4.67), 10: (6.67, 4.67), 11: (7.33, 4.67), 12: (8.0, 4.67)},
}
PAPER_INCHES = {1: (8.5, 11.0), 3: (11.0, 17.0), 5: (8.5, 14.0), 9: (8.27, 11.69)}  # short, long side


def _print_scale(ws, default_font) -> float:
    """Scale Excel applies at print: fixed, or the tighter of fit-to-width and fit-to-height.
    An absent fitToWidth or fitToHeight means one page, as Excel reads it."""
    setup = ws.page_setup
    props = ws.sheet_properties.pageSetUpPr
    if not (props is not None and props.fitToPage):
        return (setup.scale or 100) / 100
    pages_wide = 1 if setup.fitToWidth is None else int(setup.fitToWidth)
    pages_tall = 1 if setup.fitToHeight is None else int(setup.fitToHeight)
    c0, r0, c1, r1 = _print_bounds(ws)
    short, long_ = PAPER_INCHES.get(int(setup.paperSize or 1), PAPER_INCHES[1])
    landscape = setup.orientation == "landscape"
    paper_w, paper_h = (long_, short) if landscape else (short, long_)
    margins = ws.page_margins
    scale = 1.0
    if pages_wide >= 1:
        mdw, pad = DIGIT_WIDTH_PX.get(default_font.name, {}).get(int(default_font.sz or 11), (7.33, 4.67))
        total_px = 0.0
        for col in range(c0, c1 + 1):
            dim = ws.column_dimensions.get(get_column_letter(col))
            width = dim.width if dim is not None and dim.width else 8.43
            total_px += width * mdw + pad
        printable_w = (paper_w - margins.left - margins.right) * 72 * pages_wide
        if total_px:
            scale = min(scale, printable_w / (total_px * 0.75))
    if pages_tall >= 1:
        default_h = ws.sheet_format.defaultRowHeight or 15
        total_h = sum(
            (ws.row_dimensions[r].height if r in ws.row_dimensions and ws.row_dimensions[r].height else default_h)
            for r in range(r0, r1 + 1)
        )
        printable_h = (paper_h - margins.top - margins.bottom) * 72 * pages_tall
        if total_h:
            scale = min(scale, printable_h / total_h)
    return scale


def _print_bounds(ws) -> tuple[int, int, int, int]:
    area = ws.print_area
    if isinstance(area, (list, tuple)):
        area = area[0] if area else None
    ref = area.split("!")[-1].replace("$", "") if area else ws.dimensions
    return range_boundaries(ref)


def _check_printed_size(ws, default_font) -> list[dict]:  # XL18
    """Any printed line - numbers, labels, footnotes - below the floor once the page scales."""
    c0, r0, c1, r1 = _print_bounds(ws)
    sizes = [
        float(cell.font.sz or default_font.sz or 11)
        for row in ws.iter_rows(min_row=r0, max_row=r1, min_col=c0, max_col=c1)
        for cell in row
        if cell.value is not None and cell.value != ""
    ]
    if not sizes:
        return []
    scale = _print_scale(ws, default_font)
    printed = min(sizes) * scale
    if printed >= MIN_PRINTED_PT:
        return []
    return [
        _finding(
            "XL18",
            ws.title,
            f"smallest text prints at about {printed:.1f}pt ({min(sizes):g}pt at {scale:.0%} scale); "
            f"at least {MIN_PRINTED_PT:g}pt - narrow or drop columns, raise small text to body size, "
            "or use larger paper",
        )
    ]


def _side_key(side) -> tuple | None:
    if side is None or not side.style:
        return None
    color = side.color.rgb if side.color is not None and side.color.type == "rgb" else None
    return (side.style, color)


def _check_shared_edges(ws) -> list[dict]:  # XL17
    """Excel draws one line per shared edge. Two cells that each declare it differently
    render whichever wins, so a status box or total rule shows the neighbour's color."""
    hits = []
    cells = ws._cells  # noqa: SLF001 - includes border-only cells that hold no value
    for (row, col), cell in cells.items():
        pairs = (
            (cell.border.right, cells.get((row, col + 1)), "left"),
            (cell.border.bottom, cells.get((row + 1, col)), "top"),
        )
        for own, neighbour, their_side in pairs:
            mine = _side_key(own)
            theirs = _side_key(getattr(neighbour.border, their_side)) if neighbour is not None else None
            if mine and theirs and mine != theirs:
                hits.append(cell.coordinate)
                break
    if not hits:
        return []
    return [
        _finding(
            "XL17",
            ws.title,
            f"conflicting shared border edge at {_fmt_examples(sorted(set(hits)))}; "
            "declare each shared edge on one cell only",
        )
    ]


def lint_workbook(path: Path) -> list[dict]:
    wb = load_workbook(path)
    findings: list[dict] = []
    findings.extend(_check_tab_names(wb))
    findings.extend(_check_font_sprawl(wb))
    findings.extend(_check_approved_faces(wb))
    findings.extend(_check_fill_sprawl(wb))
    findings.extend(_check_tab_rainbow(wb))
    for ws in _visible_sheets(wb):
        findings.extend(_check_gridlines(ws))
        findings.extend(_check_merged(ws))
        findings.extend(_check_pure_black(ws))
        findings.extend(_check_general_numbers(ws))
        findings.extend(_check_freeze(ws))
        findings.extend(_check_parked(ws))
        findings.extend(_check_gradient_fill(ws))
        findings.extend(_check_smooth_conditional_formats(ws))
        findings.extend(_check_proportional_figures(ws))
        findings.extend(_check_bloat(ws))
        findings.extend(_check_border_grid(ws))
        findings.extend(_check_shared_edges(ws))
        findings.extend(_check_printed_size(ws, wb._fonts[0]))  # noqa: SLF001 - the default font record
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    if not args.workbook.is_file():
        print(f"error: not a file: {args.workbook}", file=sys.stderr)
        return 1
    try:
        findings = lint_workbook(args.workbook)
    except Exception as exc:  # noqa: BLE001 - report any unreadable workbook as exit 1
        print(f"error: could not lint {args.workbook}: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(json.dumps({"workbook": str(args.workbook), "findings": findings}, indent=2))
    else:
        for f in findings:
            where = f["sheet"] or "workbook"
            print(f"{f['rule']} [{where}] {f['detail']}")
        print(f"{len(findings)} finding(s)")
    return 2 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
