#!/usr/bin/env python3
"""Thin structural inventory of a planning workbook.

Deliberately shallow: it reports what tabs exist and what shape they are in.
It does NOT extract formulas or build a cross-tab dependency graph.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook


def _is_formula(value) -> bool:
    return isinstance(value, str) and value.startswith("=")


def _is_hardcoded_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _cell_counts(ws) -> tuple[int, int]:
    """Return (formula_cells, hardcoded_number_cells) for one worksheet.

    Text labels count as neither: they are structure, not inputs. Only numeric
    literals are 'hardcodes' for this ratio.
    """
    formulas = 0
    values = 0
    for row in ws.iter_rows():
        for cell in row:
            if _is_formula(cell.value):
                formulas += 1
            elif _is_hardcoded_number(cell.value):
                values += 1
    return formulas, values


def _is_label(value) -> bool:
    return isinstance(value, str) and value.strip() != "" and not value.startswith("=")


def _header_row(ws):
    """The row that most looks like a column header.

    Widest run of text labels wins; earliest row breaks a tie. Picking the
    *first* row with any text instead would select a one-cell title row, which
    real planning workbooks almost always have above the real header.
    """
    best = None
    best_width = 0
    for row in ws.iter_rows():
        width = sum(1 for cell in row if _is_label(cell.value))
        if width > best_width:
            best = row
            best_width = width
    return best


def _dimensions(header_row) -> list[str]:
    if header_row is None:
        return []
    return [cell.value.strip() for cell in header_row if _is_label(cell.value)]


# A column is a dimension candidate when, below a text header, its values are
# text and at least one value repeats. That is a shape heuristic, not proof of a
# real dimension — see DIMENSION_CANDIDATE_NOTE.
MIN_DISTINCT = 2
MAX_SAMPLE_VALUES = 10


def _data_block_end(ws, header_index: int) -> int:
    """Last row of the contiguous data block under the header.

    A fully blank row ends the table. Prose notes parked below that gap are
    commentary, not dimension values, and must not enter the value set.
    """
    last = header_index
    for row in ws.iter_rows(min_row=header_index + 1):
        if all(cell.value is None or str(cell.value).strip() == "" for cell in row):
            break
        last = row[0].row
    return last


def _dimension_candidates(ws, header_row) -> list[dict]:
    if header_row is None:
        return []

    header_index = header_row[0].row
    block_end = _data_block_end(ws, header_index)
    candidates = []

    for cell in header_row:
        if not _is_label(cell.value):
            continue
        column = cell.column
        label = cell.value.strip()

        text_values = []
        has_number = False
        for row in ws.iter_rows(
            min_row=header_index + 1,
            max_row=block_end,
            min_col=column,
            max_col=column,
        ):
            value = row[0].value
            if _is_hardcoded_number(value):
                has_number = True
                break
            if _is_label(value):
                text_values.append(value.strip())

        if has_number or not text_values:
            continue

        distinct = sorted(set(text_values))
        if len(distinct) < MIN_DISTINCT or len(distinct) == len(text_values):
            continue

        candidates.append(
            {
                "tab": ws.title,
                "column": label,
                "distinct_values": len(distinct),
                "row_count": len(text_values),
                "sample_values": distinct[:MAX_SAMPLE_VALUES],
            }
        )

    return candidates


def _tab_report(ws, header_row) -> dict:
    formulas, values = _cell_counts(ws)
    total = formulas + values
    ratio = round(values / total, 4) if total else None
    return {
        "name": ws.title,
        "formula_cells": formulas,
        "value_cells": values,
        "hardcode_ratio": ratio,
        "dimensions": _dimensions(header_row),
    }


def _named_ranges(wb) -> list[dict]:
    names = [
        {"name": name, "scope": "workbook", "refers_to": dn.attr_text or ""}
        for name, dn in wb.defined_names.items()
    ]
    for ws in wb.worksheets:
        for name, dn in ws.defined_names.items():
            names.append(
                {"name": name, "scope": ws.title, "refers_to": dn.attr_text or ""}
            )
    return names


# An external reference is a bracketed workbook token inside a formula:
#   [1]Prior!$B$4          — indexed link to another workbook
#   'C:\path\[FY26.xlsx]Sheet1'!$C$9  — explicit path
_EXTERNAL_REF = re.compile(r"\[[^\]]+\]")


def _external_links(wb, named_ranges: list[dict]) -> list[dict]:
    """External workbook references, from cell formulas AND from defined names.

    Legacy client workbooks carry most of theirs in stale defined names, so
    scanning cells alone reports 'none' on a workbook that is full of them.
    """
    links = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if not _is_formula(cell.value):
                    continue
                if _EXTERNAL_REF.search(cell.value):
                    links.append(
                        {
                            "source": f"{ws.title}!{cell.coordinate}",
                            "cell": f"{ws.title}!{cell.coordinate}",
                            "formula": cell.value,
                        }
                    )

    for nr in named_ranges:
        if _EXTERNAL_REF.search(nr["refers_to"]):
            links.append(
                {
                    "source": f"defined name: {nr['name']}",
                    "cell": None,
                    "formula": nr["refers_to"],
                }
            )

    return links


HEADER_NOTE = (
    "Header detection is HEURISTIC: the widest run of text labels on a tab is "
    "taken as its header row. A tab with no header row will show a data row "
    "here instead. Read the tab before trusting the list."
)

DIMENSION_CANDIDATE_NOTE = (
    "Dimension-candidate detection is HEURISTIC: it flags text columns whose "
    "values repeat under a text header. It does not know which columns are real "
    "dimensions in the tenant. Confirm every candidate against the tenant with "
    "`dr templates get` and `dr templates distinct` before designing a split on it."
)


def inventory(path: Path) -> dict:
    wb = load_workbook(path, data_only=False, read_only=False)

    tabs = []
    candidates = []
    for ws in wb.worksheets:
        header_row = _header_row(ws)
        tabs.append(_tab_report(ws, header_row))
        candidates.extend(_dimension_candidates(ws, header_row))

    named_ranges = _named_ranges(wb)
    report = {
        "file": path.name,
        "tabs": tabs,
        "named_ranges": named_ranges,
        "external_links": _external_links(wb, named_ranges),
        "dimension_candidates": candidates,
        "dimension_candidates_note": DIMENSION_CANDIDATE_NOTE,
        "header_note": HEADER_NOTE,
    }
    wb.close()
    return report


def _format_ratio(ratio) -> str:
    return "n/a" if ratio is None else f"{ratio:.0%}"


def render_text(report: dict) -> str:
    lines = [
        f"# Workbook inventory — {report['file']}",
        "",
        "Structural only. No formulas were extracted and no cross-tab dependency",
        "graph was built.",
        "",
        "## Tabs",
        "",
        "| Tab | Formula cells | Hardcoded numbers | Hardcode ratio |",
        "|---|---:|---:|---:|",
    ]
    for tab in report["tabs"]:
        lines.append(
            f"| {tab['name']} | {tab['formula_cells']} | {tab['value_cells']} "
            f"| {_format_ratio(tab['hardcode_ratio'])} |"
        )

    lines += ["", "## Dimensions per tab", "", report["header_note"], ""]
    for tab in report["tabs"]:
        dims = ", ".join(tab["dimensions"]) if tab["dimensions"] else "(no text header)"
        lines.append(f"- **{tab['name']}** — {dims}")

    lines += ["", "## Named ranges", ""]
    if report["named_ranges"]:
        for nr in report["named_ranges"]:
            lines.append(f"- `{nr['name']}` ({nr['scope']}) → {nr['refers_to']}")
    else:
        lines.append("- none")

    lines += ["", "## External links", ""]
    if report["external_links"]:
        for link in report["external_links"]:
            lines.append(f"- {link['source']} — `{link['formula']}`")
    else:
        lines.append("- none")

    lines += ["", "## Dimension candidates", "", report["dimension_candidates_note"], ""]
    if report["dimension_candidates"]:
        lines.append("| Tab | Column | Distinct | Rows | Sample values |")
        lines.append("|---|---|---:|---:|---|")
        for c in report["dimension_candidates"]:
            sample = ", ".join(c["sample_values"])
            lines.append(
                f"| {c['tab']} | {c['column']} | {c['distinct_values']} "
                f"| {c['row_count']} | {sample} |"
            )
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


EXIT_BAD_INPUT = 2


def _check_input(path: Path) -> str | None:
    """Return an operator-readable reason the file is unusable, or None."""
    if not path.exists():
        return f"{path}: not found"
    if path.suffix.lower() == ".xls":
        return (
            f"{path}: legacy .xls is not supported. Re-save as .xlsx — the "
            "Datarails add-in breaks on .xls too (knowledge: xlsx-not-xls)."
        )
    return None


def main(argv: list[str] | None = None) -> int:
    # Client workbooks carry non-ASCII names, and this report uses arrows and
    # em dashes. A cp1252 console must not turn that into a crash.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    problem = _check_input(args.workbook)
    if problem:
        sys.stderr.write(problem + "\n")
        return EXIT_BAD_INPUT

    try:
        report = inventory(args.workbook)
    except Exception as exc:  # openpyxl raises a wide family on bad containers
        sys.stderr.write(
            f"{args.workbook}: could not read as an .xlsx workbook — "
            f"{type(exc).__name__}: {exc}\n"
        )
        return EXIT_BAD_INPUT

    if args.as_json:
        sys.stdout.write(json.dumps(report, indent=2) + "\n")
    else:
        sys.stdout.write(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
