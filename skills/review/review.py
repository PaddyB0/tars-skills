#!/usr/bin/env python3
"""TARS weekly review rollup — reads task/session frontmatter, no Base views.

Emits: overdue, due-in-7-days, in-progress, stale-in-progress (>14d untouched)
tasks; hours by project and by company (sum DurationMin) from Work Sessions.

Usage:
    python review.py [--vault PATH] [--today YYYY-MM-DD]

Prints a Markdown report to stdout. The /review skill decides whether to also
write it to Notes/ (the --note behavior lives in the skill, not here).
"""
import os, re, glob, sys, argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

COMPLETE_TASK = "🟢 COMPLETE"
IN_PROGRESS = "🔵 IN PROGRESS"
DURATION_CUTOFF = datetime(2026, 6, 1)
DELETION_CANDIDATE_TAG = "duplicate/meeting-source"


def fm_of(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    body = text[4:end] if text[3] == "\n" else text[3:end]
    fm = {}
    for ln in body.split("\n"):
        m = re.match(r'^([^\s:#][^:]*?):\s?(.*)$', ln)
        if m:
            k, v = m.group(1).strip(), m.group(2).strip()
            if k not in fm:  # first wins; dup keys are a lint concern, not here
                fm[k] = v
    return fm


def unquote_link(v):
    m = re.search(r'\[\[([^\]|#]+)', v or "")
    return m.group(1).strip() if m else (v or "").strip('"')


def parse_date(v):
    if not v:
        return None
    v = v.strip().strip('"')
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None


def has_frontmatter_tag(text, tag):
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    frontmatter = text[:end] if end >= 0 else text
    return tag in frontmatter


def session_rollups(session_files):
    """Return post-cutoff raw and per-session rounded-billable minute totals."""
    by_proj, by_co = {}, {}
    by_proj_rounded, by_co_rounded = {}, {}
    total_min = 0
    total_rounded = 0
    included = 0
    for f in session_files:
        text = Path(f).read_text(encoding="utf-8")
        if has_frontmatter_tag(text, DELETION_CANDIDATE_TAG):
            continue
        fm = fm_of(text)
        start = parse_date(fm.get("StartTime", ""))
        if start is None or start < DURATION_CUTOFF:
            continue
        try:
            mins = int(float(fm.get("DurationMin", "") or 0))
        except ValueError:
            mins = 0
        rounded = ((mins + 29) // 30) * 30 \
            if fm.get("HoursType") == "Billable" and mins > 0 else 0
        project = unquote_link(fm.get("Project", "")) or "(unlinked)"
        company = unquote_link(fm.get("Company", "")) or "(unlinked)"
        included += 1
        total_min += mins
        total_rounded += rounded
        by_proj[project] = by_proj.get(project, 0) + mins
        by_co[company] = by_co.get(company, 0) + mins
        by_proj_rounded[project] = by_proj_rounded.get(project, 0) + rounded
        by_co_rounded[company] = by_co_rounded.get(company, 0) + rounded
    return {
        "included": included,
        "raw_min": total_min,
        "rounded_billable_min": total_rounded,
        "by_project": by_proj,
        "by_company": by_co,
        "by_project_rounded": by_proj_rounded,
        "by_company_rounded": by_co_rounded,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=os.getcwd())
    ap.add_argument("--today", default=None)
    args = ap.parse_args()
    os.chdir(args.vault)
    today = datetime.strptime(args.today, "%Y-%m-%d") if args.today else datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    soon = today + timedelta(days=7)
    stale_cut = today - timedelta(days=14)

    overdue, due_soon, in_prog, stale = [], [], [], []
    for f in glob.glob("Tasks/*.md"):
        fm = fm_of(open(f, encoding="utf-8").read())
        name = os.path.splitext(os.path.basename(f))[0]
        status = fm.get("Status", "")
        due = parse_date(fm.get("DueDate", ""))
        mod = parse_date(fm.get("modified", ""))
        proj = unquote_link(fm.get("Project", ""))
        row = {"name": name, "status": status, "due": due, "proj": proj}
        if status != COMPLETE_TASK and due and due < today:
            overdue.append(row)
        elif status != COMPLETE_TASK and due and today <= due <= soon:
            due_soon.append(row)
        if status == IN_PROGRESS:
            in_prog.append(row)
            if mod and mod < stale_cut:
                stale.append({**row, "mod": mod})

    rollup = session_rollups(glob.glob("Work Sessions/*.md"))
    by_proj, by_co = rollup["by_project"], rollup["by_company"]

    def hrs(m):
        return f"{m/60:.1f}h"

    def tasklist(rows, show_due=True):
        if not rows:
            return "- _(none)_"
        out = []
        for r in sorted(rows, key=lambda x: (x["due"] or datetime.max)):
            d = r["due"].strftime("%Y-%m-%d") if r["due"] else "—"
            suffix = f" · due {d}" if show_due else ""
            proj = f" · {r['proj']}" if r["proj"] else ""
            out.append(f"- [[{r['name']}]]{suffix}{proj}")
        return "\n".join(out)

    print(f"# TARS Weekly Review — {today.strftime('%Y-%m-%d')}\n")
    print(f"## Overdue ({len(overdue)})\n{tasklist(overdue)}\n")
    print(f"## Due in 7 days ({len(due_soon)})\n{tasklist(due_soon)}\n")
    print(f"## In progress ({len(in_prog)})\n{tasklist(in_prog)}\n")
    print(f"## Stale in progress — untouched >14d ({len(stale)})")
    if stale:
        for r in sorted(stale, key=lambda x: x["mod"]):
            print(f"- [[{r['name']}]] · last touched {r['mod'].strftime('%Y-%m-%d')}")
    else:
        print("- _(none)_")
    print(f"\n## Duration reporting — 2026-06-01+ ({rollup['included']} sessions)")
    print(f"- Raw hours: {hrs(rollup['raw_min'])}")
    print(f"- Rounded billable hours: {hrs(rollup['rounded_billable_min'])}")
    print("\n### Hours by project")
    for k, v in sorted(by_proj.items(), key=lambda kv: -kv[1]):
        rounded = rollup["by_project_rounded"].get(k, 0)
        print(f"- {k}: raw {hrs(v)} · rounded billable {hrs(rounded)}")
    print(f"\n### Hours by company")
    for k, v in sorted(by_co.items(), key=lambda kv: -kv[1]):
        rounded = rollup["by_company_rounded"].get(k, 0)
        print(f"- {k}: raw {hrs(v)} · rounded billable {hrs(rounded)}")


if __name__ == "__main__":
    main()
