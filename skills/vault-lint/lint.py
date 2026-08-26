#!/usr/bin/env python3
"""TARS vault linter — validates every note against the live fileClasses.

Re-derived (Phase 1) from Administrator/FileClasses/{task,project,milestone,session,
meeting,crm_company,crm_contacts}.md. Checks, per note:
  - frontmatter present and parseable
  - fileClass present and correct for its folder
  - no duplicate / malformed frontmatter keys
  - enum fields hold exact allowed values (emoji/case/spacing exact)
  - date fields parse as YYYY-MM-DD or YYYY-MM-DD HH:mm, never ""
  - wikilink fields resolve to a real note in the vault
  - filename matches the fileClass naming convention (warning only)

Usage:
    python lint.py [--fix] [--vault PATH]

Exit code 0 = clean, 1 = issues found. --fix applies MECHANICAL fixes only
(empty-string dates -> omitted; nothing judgment-y).
"""
import os, re, glob, sys, argparse, subprocess

# Windows consoles default to cp1252 and choke on the vault's emoji enums.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------- schema contract (source of truth: Administrator/FileClasses) ----------
ENUMS = {
    "task": {
        "Status": {"⚪ TO DO", "🔵 IN PROGRESS", "🟢 COMPLETE"},
        "Priority": {"Low", "Medium", "High", "Critical"},
        "Phase": {"Kick-Off", "Change Planning", "Workspace Configuration",
                  "Model Builds", "Dashboard Design", "Training + Enablement"},
        "Visibility": {"client facing", "internal"},
        "Executor": {"Patrick", "Code-Mac", "Code-Win", "Code-Work", "Cowork"},
        "Repeat": {"daily", "weekly", "monthly", "yearly"},
    },
    "project": {
        "Status": {"🟠 backlog", "⚪ planned", "🔵 active", "🔴 at risk", "🟢 complete"},
        "Type": {"Premium Success", "CS Hours"},
        "ScopeCategory": {"40+ hrs", "26-39 hrs", "11-25 hrs", "0-10 hrs"},
        "HubIcon": {"rocket", "folder-kanban", "briefcase-business",
                    "chart-no-axes-column", "building-2", "target", "sparkles", "wrench"},
        "HubColor": {"blue", "green", "purple", "cyan",
                     "orange", "pink", "yellow", "red"},
    },
    "session": {
        "HoursType": {"Billable", "Non-billable"},
        "ActivityType": {"Meeting", "Build", "Admin"},
        "Audience": {"External", "Internal"},
        "ReportingBucket": {"Client Delivery", "Internal Operations", "TARS / OS"},
    },
    "meeting": {
        "CallType": {"internal call", "external call"},
        "ReportingBucket": {"Client Delivery", "Internal Operations", "TARS / OS"},
        "CalendarProvider": {"reclaim", "google", "outlook"},
    },
    "crm_company": {
        "Type": {"Company", "Contact"},
        "Timezone": {"EST", "PST", "MST", "CDT"},
    },
    "crm_contacts": {
        "contact.recordtype": {"Decision Maker", "Champion", "Contact"},
        "Type": {"Company", "Contact"},
        "Timezone": {"EST", "PST", "MST", "CDT"},
    },
}
FILECLASS_TAG = {
    "task": "task",
    "project": "project",
    "milestone": "milestone",
    "session": "session",
    "meeting": "meeting",
    "crm_company": "crm_company",
    "crm_contacts": "crm_contact",
}
# date fields -> True if time component allowed
DATE_FIELDS = {
    "StartDate": True, "DueDate": True,
    "StartTime": True, "EndTime": True,
    "Completed_At": True, "created": False,
    "IngestedAt": True, "DossierUpdated": False,
    "RepeatUntil": False, "BonusAssignedAt": False, "BonusLiveAt": False,
    "TargetDate": False,
}
LINK_FIELDS = {"Project", "Parent", "BlockedBy", "Company", "Contact", "Contacts",
               "Assignee", "Task", "ContactName", "Sessions", "Meeting", "Milestone"}
LEGACY_SESSION_FIELDS = {
    "TaskName", "ProjectName", "StartDate", "EndDate", "SessionType", "Completed"
}
DELETION_CANDIDATE_TAG = "duplicate/meeting-source"
FOLDERS = {
    "task": "Tasks",
    "project": "Projects",
    "milestone": "Milestones",
    "session": "Work Sessions",
    "meeting": "Meetings",
    "crm_company": "CRM/Clients",
    "crm_contacts": "CRM/Contacts",
}
# filename convention per fileClass: (regex, human description)
NAME_RE = {
    "session": (re.compile(r"^.+ - WS \d{4}-\d{2}-\d{2} \d{4}( \(\d+\))?$"),
                "<Client> - WS YYYY-MM-DD HHmm"),
    "meeting": (re.compile(r"^.+ \(\d{4}-\d{2}-\d{2}\)$"),
                "<Client> - <Kind> (YYYY-MM-DD)"),
    "milestone": (re.compile(r"^.+ - MS - .+$"),
                  "<Project> - MS - <Milestone name>"),
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$")
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_frontmatter(text):
    """Return (dict, duplicate_keys, malformed_keys, raw_lines, span) or (None,...).

    Values: scalars are strings (quotes stripped); block lists and inline [..]
    lists become Python lists of strings.
    """
    if not text.startswith("---"):
        return None, [], [], None, None
    end = text.find("\n---", 3)
    if end == -1:
        return None, [], [], None, None
    body = text[4:end] if text[3] == "\n" else text[3:end]
    lines = body.split("\n")
    fm, dup, malformed = {}, [], []
    i = 0
    keyline = re.compile(r'^([^\s:#][^:]*?):\s?(.*)$')
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.lstrip().startswith("#"):
            i += 1
            continue
        m = keyline.match(ln)
        if not m:
            i += 1
            continue
        key = m.group(1).strip()
        val = m.group(2).strip()
        # malformed key: leftover quote or trailing colon inside the key
        if key.startswith('"') or key.endswith('"') or key.endswith(':'):
            malformed.append(key)
        if key in fm:
            dup.append(key)
        if val == "" and i + 1 < len(lines) and re.match(r'^\s*-\s', lines[i + 1]):
            # block list
            items = []
            i += 1
            while i < len(lines) and re.match(r'^\s*-\s', lines[i]):
                items.append(_strip(lines[i].split("-", 1)[1].strip()))
                i += 1
            fm[key] = items
            continue
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [_strip(x.strip()) for x in inner.split(",")] if inner else []
        else:
            fm[key] = _strip(val)
        i += 1
    return fm, dup, malformed, lines, (0, end)


def _strip(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def links_in(v):
    """All wikilink targets in a scalar or list value."""
    out = []
    vals = v if isinstance(v, list) else [v]
    for item in vals:
        if not isinstance(item, str):
            continue
        out += re.findall(r'\[\[([^\]|#]+)', item)
    return [t.strip() for t in out if t.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--vault", default=os.getcwd())
    args = ap.parse_args()
    os.chdir(args.vault)

    all_notes = set()
    for p in glob.glob("**/*.md", recursive=True):
        if ".obsidian" in p or p.replace("\\", "/").startswith("Administrator"):
            continue
        all_notes.add(os.path.splitext(os.path.basename(p))[0])

    errors, warnings = [], []
    n_notes = 0
    fixed = 0

    # bridge bookkeeping: cowork_client -> [note basenames]
    company_by_client = {}
    project_by_client = {}
    cowork_refs = []  # (rel, cowork_client) seen on any note
    projects = {}
    tasks = []
    milestones = {}

    for fc, folder in FOLDERS.items():
        pattern = os.path.join(folder, "**", "*.md") if fc == "project" \
            else os.path.join(folder, "*.md")
        for f in sorted(glob.glob(pattern, recursive=True)):
            n_notes += 1
            rel = f.replace("\\", "/")
            base = os.path.splitext(os.path.basename(f))[0]
            try:
                text = open(f, encoding="utf-8").read()
            except Exception as e:
                errors.append((rel, f"READ ERROR: {e}"))
                continue
            fm, dup, malformed, lines, span = parse_frontmatter(text)
            if fm is None:
                errors.append((rel, "no / unterminated YAML frontmatter"))
                continue

            # fileClass
            if fm.get("fileClass") != fc:
                errors.append((rel, f"fileClass is {fm.get('fileClass')!r}, expected {fc!r}"))
            tags = fm.get("tags", [])
            tag_values = tags if isinstance(tags, list) else ([tags] if tags else [])
            expected_tag = FILECLASS_TAG[fc]
            if expected_tag not in tag_values:
                errors.append((rel, f"tags must include canonical {expected_tag!r} for fileClass {fc!r}"))
            # bridge bookkeeping
            cw = fm.get("cowork_client")
            if isinstance(cw, str) and cw.strip():
                cowork_refs.append((rel, cw.strip()))
                if fc == "crm_company":
                    company_by_client.setdefault(cw.strip(), []).append(base)
                elif fc == "project":
                    project_by_client.setdefault(cw.strip(), []).append(base)
            # duplicate / malformed keys
            for d in dup:
                errors.append((rel, f"duplicate key: {d}"))
            for mk in malformed:
                errors.append((rel, f"malformed key: {mk!r}"))
            # enums
            for field, valid in ENUMS.get(fc, {}).items():
                v = fm.get(field)
                vals = v if isinstance(v, list) else ([v] if v else [])
                for item in vals:
                    if item and item not in valid:
                        errors.append((rel, f"invalid {field}: {item!r} (allowed: {sorted(valid)})"))
            if fc in {"session", "meeting"} and not fm.get("ReportingBucket"):
                warnings.append((rel, "missing required ReportingBucket — resolve in "
                                      "Activities.base#Exceptions"))
            if fc == "milestone" and not fm.get("Project"):
                errors.append((rel, "milestone requires Project"))
            if fc == "session":
                legacy = sorted(LEGACY_SESSION_FIELDS.intersection(fm))
                if legacy:
                    errors.append((rel, f"legacy session field(s) after physical migration: {legacy}"))
                tags = fm.get("tags", [])
                tagged_delete = DELETION_CANDIDATE_TAG in (
                    tags if isinstance(tags, list) else [tags]
                )
                if not tagged_delete and not (fm.get("Task") or fm.get("Meeting")):
                    warnings.append((rel, "session requires at least Task or Meeting — resolve in "
                                          "Activities.base#Exceptions"))
                for field in ("HoursType", "ActivityType", "Audience", "StartTime",
                              "EndTime", "DurationMin"):
                    if not fm.get(field) and not tagged_delete:
                        warnings.append((rel, f"missing session {field} — resolve in "
                                              "Activities.base#Exceptions"))
            # dates
            for field, allow_time in DATE_FIELDS.items():
                if field not in fm:
                    continue
                v = fm[field]
                if v == "":
                    continue  # omitted — fine
                if isinstance(v, list):
                    continue
                if v.strip('"') == "":
                    errors.append((rel, f"empty-string date {field} (use an omitted value, not \"\")"))
                    if args.fix:
                        text = re.sub(rf'(?m)^{re.escape(field)}:\s*""\s*$', f"{field}:", text)
                        fixed += 1
                elif not DATE_RE.match(v):
                    errors.append((rel, f"unparseable {field}: {v!r}"))
                elif not allow_time and not DATE_ONLY_RE.match(v):
                    errors.append((rel, f"{field} must be date-only (YYYY-MM-DD): {v!r}"))
            # wikilink resolution
            for field in LINK_FIELDS:
                if field not in fm:
                    continue
                for tgt in links_in(fm[field]):
                    if tgt not in all_notes:
                        errors.append((rel, f"unresolved link {field} -> [[{tgt}]]"))
            # filename convention (warning)
            if fc in NAME_RE:
                rx, desc = NAME_RE[fc]
                if not rx.match(base):
                    warnings.append((rel, f"filename does not match convention '{desc}'"))

            if args.fix and 'text' in dir() and text != open(f, encoding="utf-8").read():
                open(f, "w", encoding="utf-8", newline="\n").write(text)

            if fc == "project":
                projects[base] = fm
            elif fc == "task":
                tasks.append((base, fm))
            elif fc == "milestone":
                milestones[base] = (rel, fm)

    # Typed Project/Milestone relationships and same-project ownership.
    for mbase, (rel, fm) in milestones.items():
        project_links = links_in(fm.get("Project", ""))
        if len(project_links) != 1:
            errors.append((rel, "milestone Project must contain exactly one project wikilink"))
            continue
        project = project_links[0]
        if project not in projects:
            errors.append((rel, f"milestone Project must target a project note, got [[{project}]]"))
            continue
        expected_prefix = f"{project} - MS - "
        if not mbase.startswith(expected_prefix) or not mbase[len(expected_prefix):].strip():
            warnings.append((rel, f"milestone filename must start with linked project "
                                  f"'{expected_prefix}' and include a name"))

    for tbase, fm in tasks:
        if not fm.get("Milestone"):
            continue
        rel = f"Tasks/{tbase}.md"
        milestone_links = links_in(fm["Milestone"])
        if len(milestone_links) != 1:
            errors.append((rel, "Task.Milestone must contain exactly one milestone wikilink"))
            continue
        milestone = milestone_links[0]
        milestone_record = milestones.get(milestone)
        if milestone_record is None:
            errors.append((rel, f"Task.Milestone must target a milestone note, got [[{milestone}]]"))
            continue
        task_projects = links_in(fm.get("Project", ""))
        milestone_projects = links_in(milestone_record[1].get("Project", ""))
        if len(task_projects) != 1:
            errors.append((rel, "task with Milestone must contain exactly one Project wikilink"))
        elif len(milestone_projects) == 1 and task_projects[0] != milestone_projects[0]:
            errors.append((rel, f"task Project [[{task_projects[0]}]] does not match "
                                f"milestone Project [[{milestone_projects[0]}]]"))

    # ---- bridge checks (Cowork <-> vault) ----
    clients_root = os.path.join("Cowork", "clients")
    if os.path.isdir(clients_root):
        folders = sorted(
            d for d in os.listdir(clients_root)
            if os.path.isdir(os.path.join(clients_root, d)) and d != "_template"
        )
        folder_set = set(folders)

        # 1) every cowork_client: on a note must resolve to a real client folder
        for rel, cw in cowork_refs:
            if cw not in folder_set:
                errors.append((rel, f"cowork_client: {cw!r} has no Cowork/clients/{cw}/ folder"))

        ptr_re = re.compile(r"\*\*TARS project:\*\*\s*(.+?)\s*(?:·.*)?$", re.M)
        cpr_re = re.compile(r"\*\*TARS company:\*\*\s*(.+?)\s*$", re.M)
        for folder in folders:
            frel = f"Cowork/clients/{folder}/CLAUDE.md"

            # 2) exactly one company note points here
            comps = company_by_client.get(folder, [])
            if not comps:
                errors.append((frel, f"client folder has no CRM company note "
                                     f"(no crm_company with cowork_client: {folder!r})"))
            elif len(comps) > 1:
                errors.append((frel, f"multiple company notes claim cowork_client {folder!r}: {comps}"))

            # 3) client CLAUDE.md carries resolvable bidirectional pointers
            cpath = os.path.join(clients_root, folder, "CLAUDE.md")
            if not os.path.isfile(cpath):
                errors.append((frel, "client folder has no CLAUDE.md"))
                continue
            ctext = open(cpath, encoding="utf-8").read()
            pm, cm = ptr_re.search(ctext), cpr_re.search(ctext)
            if not pm:
                warnings.append((frel, "missing '**TARS project:**' pointer"))
            else:
                tgt = re.sub(r"\s*·.*$", "", pm.group(1)).strip()
                if tgt and tgt not in all_notes:
                    errors.append((frel, f"**TARS project:** -> {tgt!r} resolves to no note"))
            if not cm:
                warnings.append((frel, "missing '**TARS company:**' pointer"))
            else:
                tgt = cm.group(1).strip()
                # strip trailing parenthetical annotations like "(company-only)"
                tgt = re.sub(r"\s*_?\(.*$", "", tgt).strip()
                if tgt and tgt not in all_notes:
                    errors.append((frel, f"**TARS company:** -> {tgt!r} resolves to no note"))

    # ---- PM write-through drift check ----
    # Work that exists only under Cowork/clients/<X>/ is invisible to the PM layer.
    # Any commit in the last 7 days touching a client folder must have a same-day
    # Work Session note for that client (warning).
    try:
        gitlog = subprocess.run(
            ["git", "log", "--since=7.days", "--name-only",
             "--pretty=format:@%ad", "--date=short"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        ).stdout
    except Exception:
        gitlog = ""
    ws_days = set()  # (client, YYYY-MM-DD) with a logged Work Session
    for f in glob.glob(os.path.join("Work Sessions", "*.md")):
        m = re.match(r"^(.+) - WS (\d{4}-\d{2}-\d{2})",
                     os.path.splitext(os.path.basename(f))[0])
        if m:
            ws_days.add((m.group(1), m.group(2)))
    # group per commit so bulk admin commits (merges, renames, restructures —
    # touching many clients at once) can be skipped; build work touches 1-2.
    BULK_THRESHOLD = 3
    commits, cur = [], None
    for ln in gitlog.splitlines():
        if ln.startswith("@"):
            cur = {"day": ln[1:].strip(), "clients": set()}
            commits.append(cur)
            continue
        m = re.match(r"^Cowork/clients/([^/]+)/", ln.strip().replace("\\", "/"))
        if m and cur is not None and m.group(1) != "_template":
            cur["clients"].add(m.group(1))
    touched = set()
    for c in commits:
        if 0 < len(c["clients"]) <= BULK_THRESHOLD:
            touched.update((cl, c["day"]) for cl in c["clients"])
    # only warn about clients that exist today (renamed folders linger in history)
    live_clients = {d for d in os.listdir(clients_root)
                    if os.path.isdir(os.path.join(clients_root, d))} \
        if os.path.isdir(clients_root) else set()
    for client, day in sorted(touched):
        if client not in live_clients:
            continue
        if (client, day) not in ws_days:
            warnings.append((f"Cowork/clients/{client}/",
                             f"commit on {day} touched this client but no "
                             f"'Work Sessions/{client} - WS {day} *' note exists "
                             f"(PM write-through missed — log it with /ws)"))

    # ---- machine identity check (.ai-os-machine drives /catchup routing) ----
    mfile = os.path.join("Cowork", ".ai-os-machine")
    if os.path.isfile(mfile):
        label = open(mfile, encoding="utf-8").read().strip()
        valid = ENUMS["task"]["Executor"]
        if label not in valid:
            errors.append(("Cowork/.ai-os-machine",
                           f"machine label {label!r} is not a valid Executor value "
                           f"{sorted(valid)} — /catchup task routing will silently "
                           f"match nothing"))

    # ---- report ----
    print(f"TARS vault lint — {n_notes} notes across {len(FOLDERS)} fileClasses\n")
    if args.fix and fixed:
        print(f"Applied {fixed} mechanical fix(es).\n")
    if not errors and not warnings:
        print("CLEAN — no issues.")
        return 0
    if errors:
        print(f"ERRORS ({len(errors)}):")
        cur = None
        for f, m in errors:
            if f != cur:
                print(f"\n  {f}"); cur = f
            print(f"     ✗ {m}")
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        cur = None
        for f, m in warnings:
            if f != cur:
                print(f"\n  {f}"); cur = f
            print(f"     ! {m}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
