#!/usr/bin/env python3
"""Deterministic design lint for delivered .xlsx reports.

Enforces the testable subset of the excel-design contract
(references/DESIGN.md). Rules XL1-XL16. Exit codes mirror the Impeccable
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

DEFAULT_TAB_NAME = re.compile(r"^Sheet\d*$", re.IGNORECASE)
PURE_BLACK = "FF000000"
MAX_FACES = 2
MAX_SIZES = 5
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


def _check_parked(ws) -> list[dict]:  # XL9
    findings = []
    zoom = ws.sheet_view.zoomScale
    if zoom is not None and zoom != 100:
        findings.append(_finding("XL9", ws.title, f"zoom is {zoom}%; park at 100%"))
    selections = ws.sheet_view.selection
    if selections:
        active = selections[0].activeCell or selections[0].sqref
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


def _check_border_grid(ws) -> list[dict]:  # XL12 (heuristic)
    populated = 0
    boxed = 0
    for cell in _iter_value_cells(ws):
        populated += 1
        if _has_four_borders(cell):
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
