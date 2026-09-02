#!/usr/bin/env python3
"""TARS unified linter — three passes: schema (S1–S4) · propagation (P1–P8) · graph (G1–G7).

Supersedes /vault-lint (schema only) and Cowork /lint (knowledge only). Spec:
Notes/TARS Unified OS - Schema.md § 6. Schema constants are re-derived from
Administrator/FileClasses/*.md — that folder is the source of truth.

The mechanically-decidable checks live here; the judgment checks (P3, P4, G2, G4,
G6, G7 and body-link nuance) are driven by the reader per the SKILL.md, which reads
this script's output first.

Usage:
    python lint.py [--fix] [--vault PATH] [--today YYYY-MM-DD]

Exit code 0 = no errors (warnings do not fail). --fix applies MECHANICAL fixes only
(empty-string dates -> omitted).
"""
import os, re, glob, sys, argparse, subprocess, json
from datetime import date, datetime

# Windows consoles default to cp1252 and choke on the vault's emoji enums.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------- schema contract (source of truth: Administrator/FileClasses) ----------
ENUMS = {
    "task": {
        "Status": {"⚫ BACKLOG", "⚪ TO DO", "🔵 IN PROGRESS",
                   "🟣 HUMAN REVIEW", "🟠 REWORK", "🟢 MERGING",
                   "🟢 COMPLETE", "⚫ CANCELED", "⚫ DUPLICATE"},
        "Priority": {"Low", "Medium", "High", "Critical"},
        "Phase": {"Kick-Off", "Change Planning", "Workspace Configuration",
                  "Model Builds", "Dashboard Design", "Training + Enablement"},
        "Visibility": {"client facing", "internal"},
        "Executor": {"Patrick", "Code-Mac", "Code-Win", "Code-Work", "Cowork"},
        "Workflow": {"dr-recon", "dr-lut-diagnose"},
        "Repeat": {"daily", "weekly", "monthly", "yearly"},
        "ScheduleMode": {"flexible", "fixed", "manual"},
        "Energy": {"deep", "shallow", "any"},
    },
    "habit": {
        "Status": {"active", "paused", "retired"},
        "Priority": {"Low", "Medium", "High", "Critical"},
        "Cadence": {"daily", "weekly"},
        "DaysOfWeek": {
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        },
        "CatchUpPolicy": {"skip", "rollover-once", "catch-up-capped"},
        "CalendarVisibility": {"default", "private"},
    },
    "scheduling_policy": {
        "DefaultVisibility": {"default", "private"},
        "ApplyMode": {"assisted", "automatic"},
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
    "habit": "habit",
    "scheduling_policy": "scheduling_policy",
    "project": "project",
    "milestone": "milestone",
    "session": "session",
    "meeting": "meeting",
    "crm_company": "crm_company",
    "crm_contacts": "crm_contact",
}
# Missing values remain visible in the Activities exception view rather than being
# coerced to an "Other" enum. Lint surfaces them as warnings until classified.
REQUIRED_REPORTING_BUCKET = {"session", "meeting"}
# date fields -> True if time component allowed
DATE_FIELDS = {
    "StartDate": True, "DueDate": True,
    "StartTime": True, "EndTime": True,
    "Completed_At": True, "created": False,
    "IngestedAt": True, "GongReceivedAt": True, "DossierUpdated": False,
    "RepeatUntil": False,   # Unified OS additions
    "EndDate": False,
    "BonusAssignedAt": False, "BonusLiveAt": False,
    "TargetDate": False,
}
LINK_FIELDS = {"Project", "Parent", "BlockedBy", "Company", "Contact", "Contacts",
               "Assignee", "Task", "ContactName", "Sessions", "Meeting", "Milestone",
               "SchedulingPolicy"}
LEGACY_SESSION_FIELDS = {
    "TaskName", "ProjectName", "StartDate", "EndDate", "SessionType", "Completed"
}
FOLDERS = {
    "task": "Tasks",
    "habit": "Habits",
    "scheduling_policy": "Scheduling Policies",
    "project": "Projects",
    "milestone": "Milestones",
    "session": "Work Sessions",
    "meeting": "Meetings",
    "crm_company": "CRM/Clients",
    "crm_contacts": "CRM/Contacts",
}
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
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.I,
)
TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
GONG_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} (?:[01]\d|2[0-3]):[0-5]\d$"
)
WINDOW_RE = re.compile(
    r"^((?:[01]\d|2[0-3]):[0-5]\d)-((?:[01]\d|2[0-3]):[0-5]\d)$"
)
OBSIDIAN_CONFLICT_COPY_FILENAME_RE = re.compile(
    r"^[^/\\\r\n]+ \(Conflicted copy [^/\\\r\n]+ \d{12}\)\.[^/\\\r\n]+$"
)
POLICY_WINDOW_FIELDS = (
    "MondayWindow", "TuesdayWindow", "WednesdayWindow", "ThursdayWindow",
    "FridayWindow", "SaturdayWindow", "SundayWindow",
)
POLICY_PREFERENCE_FIELDS = (
    "DeepWorkWindow", "ShallowWorkWindow", "NormalHoursWindow",
)
POLICY_POSITIVE_FIELDS = (
    "DefaultTaskMinBlockMin",
    "DefaultTaskMaxBlockMin",
    "DefaultHabitDurationMin",
    "DailyCapacityMin",
    "WeeklyCapacityMin",
)
POLICY_NONNEGATIVE_FIELDS = (
    "MeetingPrepMin",
    "TravelBufferMin",
    "DecompressionMin",
    "WorkBreakMin",
    "SoftFreezeHours",
    "HardLockHours",
)

# propagation thresholds (schema § 6)
P1_STALE_DAYS = 2      # meeting un-ingested this long
P3_STALE_DAYS = 30     # unchecked commitment this old
P7_DEAD_DAYS = 21      # fallback; freshness-policy.json is authoritative
DELETION_CANDIDATE_TAG = "duplicate/meeting-source"
DURATION_CUTOFF = date(2026, 6, 1)
P5_NON_DELIVERY_SUBJECT_PREFIXES = (
    "Clean up TARS ",
    "Ingest ",
)


def p5_subject_is_delivery(subject):
    """Return False for explicitly named OS maintenance/propagation commits."""
    return not subject.startswith(P5_NON_DELIVERY_SUBJECT_PREFIXES)


def is_obsidian_conflict_copy_filename(name):
    """Return whether *name* is an official Obsidian conflict-copy filename."""
    return isinstance(name, str) and bool(
        OBSIDIAN_CONFLICT_COPY_FILENAME_RE.fullmatch(name)
    )


def parse_frontmatter(text):
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
        if key.startswith('"') or key.endswith('"') or key.endswith(':'):
            malformed.append(key)
        colon = ln.find(":")
        if val and colon + 1 < len(ln) and ln[colon + 1] not in " \t":
            malformed.append(f"{key} (missing space after ':')")
        if ": " in val and not val.startswith(('"', "'", "|", ">")):
            malformed.append(f"{key} (unquoted value contains ': ')")
        if key in fm:
            dup.append(key)
        if val == "" and i + 1 < len(lines) and re.match(r'^\s*-\s', lines[i + 1]):
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
            parsed = _strip(val)
            if (
                key in {"GongId", "GongDurationMin"}
                and val[:1] not in {'"', "'"}
                and re.fullmatch(r"-?\d+(?:\.\d+)?", val)
            ):
                parsed = float(val) if "." in val else int(val)
            fm[key] = parsed
        i += 1
    return fm, dup, malformed, lines, (0, end)


def _strip(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def body_of(text):
    """Everything after the closing frontmatter fence."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    rest = text[end + 4:]
    nl = rest.find("\n")
    return rest[nl + 1:] if nl != -1 else ""


def links_in(v):
    out = []
    vals = v if isinstance(v, list) else [v]
    for item in vals:
        if not isinstance(item, str):
            continue
        out += re.findall(r'\[\[([^\]|#]+)', item)
    return [t.strip() for t in out if t.strip()]


def parse_dt(v):
    """Parse a schema date/datetime string to a date; None if unparseable/empty."""
    if not isinstance(v, str) or not v.strip():
        return None
    s = v.strip().strip('"')
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def as_bool(v):
    return v is True or (isinstance(v, str) and v.strip().lower() == "true")


def nonempty(v):
    return v is not None and v != "" and v != []


def as_number(v):
    if not nonempty(v) or isinstance(v, bool):
        return None
    try:
        number = float(v)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def is_positive_integer(v):
    number = as_number(v)
    return number is not None and number.is_integer() and number > 0


def is_nonnegative_integer(v):
    number = as_number(v)
    return number is not None and number.is_integer() and number >= 0


def valid_window(v):
    if not isinstance(v, str):
        return False
    match = WINDOW_RE.fullmatch(v.strip())
    return bool(match and match.group(1) < match.group(2))


def phase2_scalar_errors(fc, fm):
    """File-local Phase 2 checks shared by full lint and write-time hooks."""
    errors = []
    uid = fm.get("UID")
    if nonempty(uid) and not UUID_RE.fullmatch(str(uid).strip()):
        errors.append("UID must be a UUIDv4")

    if fc == "task":
        auto = as_bool(fm.get("AutoSchedule"))
        if auto and as_bool(fm.get("SyncToReclaim")):
            errors.append("AutoSchedule cannot be true when SyncToReclaim is true")
        if auto and not nonempty(uid):
            errors.append("AutoSchedule requires UID")
        if auto and fm.get("ScheduleMode") != "flexible":
            errors.append("AutoSchedule requires ScheduleMode: flexible")
        for field in ("MinBlockMin", "MaxBlockMin"):
            if nonempty(fm.get(field)) and not is_positive_integer(fm[field]):
                errors.append(f"{field} must be a positive integer")
        minimum = as_number(fm.get("MinBlockMin"))
        maximum = as_number(fm.get("MaxBlockMin"))
        if minimum is not None and maximum is not None and minimum > maximum:
            errors.append("MinBlockMin must be less than or equal to MaxBlockMin")
        if auto and len(links_in(fm.get("SchedulingPolicy", ""))) != 1:
            errors.append(
                "AutoSchedule requires exactly one SchedulingPolicy link "
                "to a scheduling_policy note"
            )

    elif fc == "habit":
        active = fm.get("Status") == "active"
        for field in ("TargetCount", "DurationMin"):
            if nonempty(fm.get(field)) and not is_positive_integer(fm[field]):
                errors.append(f"{field} must be a positive integer")
        for field in ("EarliestTime", "PreferredTime", "LatestTime"):
            if nonempty(fm.get(field)) and not TIME_RE.fullmatch(str(fm[field])):
                errors.append(f"{field} must be HH:mm")
        earliest = fm.get("EarliestTime")
        preferred = fm.get("PreferredTime")
        latest = fm.get("LatestTime")
        bounds_valid = all(
            nonempty(value) and TIME_RE.fullmatch(str(value))
            for value in (earliest, latest)
        )
        preferred_valid = (
            not nonempty(preferred)
            or bool(TIME_RE.fullmatch(str(preferred)))
        )
        if bounds_valid and preferred_valid:
            outside_order = earliest > latest
            if nonempty(preferred):
                outside_order = outside_order or not (
                    earliest <= preferred <= latest
                )
            if outside_order:
                errors.append(
                    "habit time order must be "
                    "EarliestTime <= PreferredTime <= LatestTime"
                )
        if nonempty(fm.get("StartDate")) and not DATE_ONLY_RE.fullmatch(str(fm["StartDate"])):
            errors.append("habit StartDate must be date-only (YYYY-MM-DD)")
        if nonempty(fm.get("EndDate")) and not DATE_ONLY_RE.fullmatch(str(fm["EndDate"])):
            errors.append("habit EndDate must be date-only (YYYY-MM-DD)")
        start = parse_dt(fm.get("StartDate", ""))
        end = parse_dt(fm.get("EndDate", ""))
        if start and end and start > end:
            errors.append("habit StartDate must be on or before EndDate")
        if active:
            if not nonempty(uid):
                errors.append("active habit requires UID")
            if not is_positive_integer(fm.get("TargetCount")):
                errors.append("active habit TargetCount must be a positive integer")
            if not is_positive_integer(fm.get("DurationMin")):
                errors.append("active habit DurationMin must be a positive integer")
            if fm.get("Cadence") == "weekly" and not fm.get("DaysOfWeek"):
                errors.append("weekly active habit requires DaysOfWeek")
            if len(links_in(fm.get("SchedulingPolicy", ""))) != 1:
                errors.append(
                    "active habit requires exactly one SchedulingPolicy link "
                    "to a scheduling_policy note"
                )
            if not bounds_valid:
                errors.append(
                    "active habit requires EarliestTime and LatestTime in HH:mm"
                )

    elif fc == "scheduling_policy":
        if not nonempty(uid):
            errors.append("scheduling policy requires UID")
        if not nonempty(fm.get("Timezone")):
            errors.append("scheduling policy requires Timezone")
        work_windows = [fm.get(field) for field in POLICY_WINDOW_FIELDS]
        if not any(nonempty(value) for value in work_windows):
            errors.append("scheduling policy requires at least one work window")
        for field in POLICY_WINDOW_FIELDS + ("MeetingWindow",):
            value = fm.get(field)
            if nonempty(value) and not valid_window(value):
                errors.append(f"invalid {field}: expected HH:mm-HH:mm with start < end")
        for field in POLICY_PREFERENCE_FIELDS:
            if field in fm and not valid_window(fm[field]):
                errors.append(
                    f"invalid {field}: expected a non-empty scalar "
                    "HH:mm-HH:mm with start < end"
                )
        if isinstance(fm.get("NoMeetingWindows"), list):
            errors.append("NoMeetingWindows must be a scalar string")
        for field in POLICY_POSITIVE_FIELDS:
            if not is_positive_integer(fm.get(field)):
                errors.append(f"{field} must be a positive integer")
        for field in POLICY_NONNEGATIVE_FIELDS:
            if not is_nonnegative_integer(fm.get(field)):
                errors.append(f"{field} must be a nonnegative integer")
        minimum = as_number(fm.get("DefaultTaskMinBlockMin"))
        maximum = as_number(fm.get("DefaultTaskMaxBlockMin"))
        if minimum is not None and maximum is not None and minimum > maximum:
            errors.append(
                "DefaultTaskMinBlockMin must be less than or equal "
                "to DefaultTaskMaxBlockMin"
            )
        hard_lock = as_number(fm.get("HardLockHours"))
        soft_freeze = as_number(fm.get("SoftFreezeHours"))
        if hard_lock is not None and soft_freeze is not None and hard_lock > soft_freeze:
            errors.append(
                "HardLockHours must be less than or equal to SoftFreezeHours"
            )
        if not nonempty(fm.get("TargetCalendar")):
            errors.append("scheduling policy requires TargetCalendar")
        if not nonempty(fm.get("DefaultVisibility")):
            errors.append("scheduling policy requires DefaultVisibility")
        if not nonempty(fm.get("ApplyMode")):
            errors.append("scheduling policy requires ApplyMode")

    elif fc == "meeting":
        gong_id = fm.get("GongId")
        gong_title = fm.get("GongTitle")
        gong_received_at = fm.get("GongReceivedAt")
        gong_duration = fm.get("GongDurationMin")
        if nonempty(gong_id) and not isinstance(gong_id, str):
            errors.append("GongId must be a scalar string")
        if nonempty(gong_title) and not isinstance(gong_title, str):
            errors.append("GongTitle must be a scalar string")
        if nonempty(gong_received_at) and not (
            isinstance(gong_received_at, str)
            and GONG_DATETIME_RE.fullmatch(gong_received_at.strip())
        ):
            errors.append("GongReceivedAt must be YYYY-MM-DD HH:mm")
        if nonempty(gong_duration) and not (
            isinstance(gong_duration, (int, float))
            and not isinstance(gong_duration, bool)
            and is_positive_integer(gong_duration)
        ):
            errors.append("GongDurationMin must be a positive integer")
        if any(nonempty(fm.get(field)) for field in (
            "GongTitle", "GongReceivedAt", "GongDurationMin"
        )) and not (isinstance(gong_id, str) and gong_id.strip()):
            errors.append("Gong metadata requires GongId")

    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--vault", default=os.getcwd())
    ap.add_argument("--today", default=None, help="override 'today' (YYYY-MM-DD)")
    args = ap.parse_args()
    os.chdir(args.vault)
    today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
    policy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "freshness-policy.json")
    with open(policy_path, encoding="utf-8") as pf:
        freshness_policy = json.load(pf)
    meeting_cutover = datetime.strptime(
        freshness_policy["meeting_knowledge_cutover"], "%Y-%m-%d").date()
    default_stale_days = freshness_policy.get(
        "default_active_client_stale_days", P7_DEAD_DAYS)
    client_freshness = freshness_policy.get("clients", {})

    # every note basename in the vault (for link resolution)
    all_notes = set()
    for p in glob.glob("**/*.md", recursive=True):
        pp = p.replace("\\", "/")
        if ".obsidian" in pp or pp.startswith("Administrator"):
            continue
        all_notes.add(os.path.splitext(os.path.basename(p))[0])

    errors, warnings = [], []
    n_notes = 0
    fixed = 0

    # Obsidian conflict copies can be any file type and can live outside mapped
    # note folders. Inspect regular filenames across the vault, but never enter
    # Git internals or traverse machine-local symlinks.
    for root, dirnames, filenames in os.walk(
        ".", topdown=True, followlinks=False
    ):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname != ".git"
            and not os.path.islink(os.path.join(root, dirname))
        ]
        for name in filenames:
            path = os.path.join(root, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            if is_obsidian_conflict_copy_filename(name):
                rel = os.path.relpath(path, ".").replace("\\", "/")
                errors.append((
                    rel,
                    "Obsidian conflict-copy filename; resolve manually "
                    "(lint never auto-fixes conflict copies)",
                ))

    company_by_client = {}
    project_by_client = {}
    cowork_refs = []

    # collected for the propagation / graph passes
    meetings = []   # (base, fm, body)
    companies = {}  # base -> fm
    projects = {}   # base -> fm
    tasks = []      # (base, fm)
    milestones = {} # base -> (relative path, fm)
    calendar_identities = {}
    gong_identities = {}
    phase2_records = []  # (relative path, fileClass, frontmatter)
    scheduling_policies = set()

    for fc, folder in FOLDERS.items():
        # projects have a Complete/ subfolder — scan it too so completed
        # engagements are still schema/graph-checked (they were escaping the flat glob)
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

            if fm.get("fileClass") != fc:
                errors.append((rel, f"fileClass is {fm.get('fileClass')!r}, expected {fc!r}"))
            tags = fm.get("tags", [])
            tag_values = tags if isinstance(tags, list) else ([tags] if tags else [])
            expected_tag = FILECLASS_TAG[fc]
            if expected_tag not in tag_values:
                errors.append((rel, f"tags must include canonical {expected_tag!r} for fileClass {fc!r}"))
            cw = fm.get("cowork_client")
            if isinstance(cw, str) and cw.strip():
                cowork_refs.append((rel, cw.strip()))
                if fc == "crm_company":
                    company_by_client.setdefault(cw.strip(), []).append(base)
                elif fc == "project":
                    project_by_client.setdefault(cw.strip(), []).append(base)
            for d in dup:
                errors.append((rel, f"duplicate key: {d}"))
            for mk in malformed:
                errors.append((rel, f"malformed YAML key/value: {mk!r}"))
            for field, valid in ENUMS.get(fc, {}).items():
                v = fm.get(field)
                vals = v if isinstance(v, list) else ([v] if v else [])
                for item in vals:
                    if item and item not in valid:
                        errors.append((rel, f"invalid {field}: {item!r} (allowed: {sorted(valid)})"))
            for message in phase2_scalar_errors(fc, fm):
                errors.append((rel, message))
            if fc in REQUIRED_REPORTING_BUCKET and not fm.get("ReportingBucket"):
                warnings.append((rel, "missing required ReportingBucket — resolve in "
                                      "Activities.base#Exceptions"))
            if fc == "milestone" and not fm.get("Project"):
                errors.append((rel, "milestone requires Project"))
            if (fc == "meeting" and parse_dt(fm.get("StartTime", "")) and
                    parse_dt(fm.get("StartTime", "")) >= DURATION_CUTOFF and
                    not fm.get("EndTime")):
                warnings.append((rel, "post-cutoff Meeting is missing EndTime; duration "
                                      "ledger creation is blocked — resolve in "
                                      "Activities.base#Exceptions"))
            if fc == "meeting":
                provider = fm.get("CalendarProvider")
                event_id = fm.get("CalendarEventID")
                if bool(provider) != bool(event_id):
                    errors.append((rel, "CalendarProvider and CalendarEventID must be written together"))
                elif provider and event_id:
                    identity = (provider, event_id)
                    earlier = calendar_identities.get(identity)
                    if earlier:
                        errors.append((rel, f"duplicate calendar identity also used by {earlier}"))
                    else:
                        calendar_identities[identity] = rel
                gong_id = fm.get("GongId")
                if isinstance(gong_id, str) and gong_id.strip():
                    normalized_gong_id = gong_id.strip()
                    earlier = gong_identities.get(normalized_gong_id)
                    if earlier:
                        errors.append((rel, f"duplicate GongId also used by {earlier}"))
                    else:
                        gong_identities[normalized_gong_id] = rel
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
            for field, allow_time in DATE_FIELDS.items():
                if field not in fm:
                    continue
                v = fm[field]
                quoted_empty = re.search(
                    rf'(?m)^{re.escape(field)}:\s*(?:""|\'\')\s*$',
                    text,
                )
                if quoted_empty:
                    errors.append((rel, f"empty-string date {field} "
                                         f"(use an omitted value, not \"\")"))
                    if args.fix:
                        text = re.sub(
                            rf'(?m)^{re.escape(field)}:\s*(?:""|\'\')\s*$',
                            f"{field}:",
                            text,
                        )
                        fixed += 1
                    continue
                if v == "" or isinstance(v, list):
                    continue
                if not DATE_RE.match(v):
                    errors.append((rel, f"unparseable {field}: {v!r}"))
                elif not allow_time and not DATE_ONLY_RE.match(v):
                    errors.append((rel, f"{field} must be date-only (YYYY-MM-DD): {v!r}"))
            for field in LINK_FIELDS:
                if field not in fm:
                    continue
                for tgt in links_in(fm[field]):
                    if tgt not in all_notes:
                        errors.append((rel, f"unresolved link {field} -> [[{tgt}]]"))
            if fc in NAME_RE:
                rx, desc = NAME_RE[fc]
                if not rx.match(base):
                    warnings.append((rel, f"filename does not match convention '{desc}'"))

            if args.fix and text != open(f, encoding="utf-8").read():
                open(f, "w", encoding="utf-8", newline="\n").write(text)

            # collect for later passes
            if fc == "meeting":
                meetings.append((base, fm, body_of(text)))
            elif fc == "crm_company":
                companies[base] = fm
            elif fc == "project":
                projects[base] = fm
            elif fc == "task":
                tasks.append((base, fm))
            elif fc == "milestone":
                milestones[base] = (rel, fm)
            if fc in {"task", "habit", "scheduling_policy"}:
                phase2_records.append((rel, fc, fm))
            if fc == "scheduling_policy":
                scheduling_policies.add(base)

    # Scheduler identities are provider-neutral and globally unique across every
    # schedulable record type. Report every colliding note so either side can be
    # repaired deliberately.
    records_by_uid = {}
    for rel, fc, fm in phase2_records:
        uid = str(fm.get("UID", "")).strip()
        if uid:
            records_by_uid.setdefault(uid, []).append((rel, fc))
    for uid, records in records_by_uid.items():
        if len(records) < 2:
            continue
        for rel, _fc in records:
            others = ", ".join(
                other_rel for other_rel, _other_fc in records if other_rel != rel
            )
            errors.append((
                rel,
                f"duplicate scheduler UID {uid} also used by {others}",
            ))

    # SchedulingPolicy is a typed relationship, not merely a resolving wikilink.
    # Legacy Tasks may omit it; opted-in Tasks and active Habits require exactly one.
    for rel, fc, fm in phase2_records:
        policy_links = links_in(fm.get("SchedulingPolicy", ""))
        required = (
            (fc == "task" and as_bool(fm.get("AutoSchedule")))
            or (fc == "habit" and fm.get("Status") == "active")
        )
        if len(policy_links) == 1 and policy_links[0] not in scheduling_policies:
            if fc == "task" and required:
                message = (
                    "AutoSchedule requires exactly one SchedulingPolicy link "
                    "to a scheduling_policy note"
                )
            elif fc == "habit" and required:
                message = (
                    "active habit requires exactly one SchedulingPolicy link "
                    "to a scheduling_policy note"
                )
            else:
                message = (
                    "SchedulingPolicy must contain exactly one wikilink "
                    "to a scheduling_policy note"
                )
            errors.append((rel, message))
        elif not required and len(policy_links) > 1:
            errors.append((
                rel,
                "SchedulingPolicy must contain exactly one wikilink "
                "to a scheduling_policy note",
            ))

    # Project/milestone/task relationship contract. Link existence alone is not
    # sufficient: each relationship must target the correct fileClass, and a
    # task may only use milestones owned by its own project.
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

    # =============================== PROPAGATION PASS ===============================
    def company_of(fm):
        ls = links_in(fm.get("Company", "")) if fm.get("Company") else []
        return ls[0] if ls else None

    # map: company basename -> [(meeting_date, ingested_bool)]
    meetings_by_company = {}
    for base, fm, body in meetings:
        co = company_of(fm)
        d = parse_dt(fm.get("StartTime", ""))
        ing = bool(str(fm.get("IngestedAt", "")).strip())
        if co:
            meetings_by_company.setdefault(co, []).append((d, ing))

        # P1: un-ingested and older than threshold
        if (not ing and d is not None and d >= meeting_cutover
                and (today - d).days > P1_STALE_DAYS):
            warnings.append((f"Meetings/{base}.md",
                             f"P1: un-ingested for {(today - d).days}d "
                             f"(StartTime {d}) — run /ingest-meeting"))
        # P6: ingested but body carries no Recap/Key Points/Next Steps content
        if ing:
            stripped = "\n".join(
                l for l in body.splitlines()
                if l.strip() and not l.lstrip().startswith("#")
                and not l.strip().startswith("![[")
            ).strip()
            if len(stripped) < 15:
                warnings.append((f"Meetings/{base}.md",
                                 "P6: ingested but body is empty (no Recap/Key Points/"
                                 "Next Steps content) — capture-pipeline failure; re-import then re-ingest"))

    # P2: company DossierUpdated older than its latest ingested meeting
    for cbase, fm in companies.items():
        du = parse_dt(fm.get("DossierUpdated", ""))
        ing_dates = [d for (d, ing) in meetings_by_company.get(cbase, []) if ing and d]
        if ing_dates:
            latest = max(ing_dates)
            if du is None or du < latest:
                warnings.append((f"CRM/Clients/{cbase}.md",
                                 f"P2: DossierUpdated ({du}) is behind latest ingested "
                                 f"meeting ({latest}) — re-run /ingest-meeting or refresh the dossier"))

    # active engagement per company (via project.Company link)
    active_project_companies = set()
    active_project_by_company = {}
    for pbase, fm in projects.items():
        st = fm.get("Status", "")
        co = company_of(fm)
        if co and st in ("🔵 active", "🔴 at risk"):
            active_project_companies.add(co)
            active_project_by_company.setdefault(co, []).append(pbase)

    # P7: cadence-aware dead-feed detection. Per-client policy lives in one JSON
    # source; stale_days=null means on-demand and suppresses feed-age alarms.
    p7_no_feed = []
    for co in sorted(active_project_companies):
        client_policy = client_freshness.get(co, {})
        stale_days = client_policy.get("stale_days", default_stale_days)
        if stale_days is None:
            continue
        dates = [d for (d, ing) in meetings_by_company.get(co, []) if d]
        if not dates:
            p7_no_feed.append(co)
        else:
            gap = (today - max(dates)).days
            if gap > stale_days:
                warnings.append((f"CRM/Clients/{co}.md",
                                 f"P7: active engagement, last meeting {gap}d ago "
                                 f"({max(dates)}; policy {stale_days}d) — verify the "
                                 f"Gong → vault feed"))
    if p7_no_feed:
        warnings.append(("(portfolio)",
                         f"P7: {len(p7_no_feed)} active client(s) have NO meetings on "
                         f"file — {', '.join(p7_no_feed)} (thin dossiers / feed not yet "
                         f"established, not a dead feed)"))

    # P8: open task whose Project is complete while its Company has an active engagement
    for tbase, fm in tasks:
        st = fm.get("Status", "")
        if st == "🟢 COMPLETE":
            continue
        for ptgt in links_in(fm.get("Project", "")) if fm.get("Project") else []:
            pfm = projects.get(ptgt)
            if pfm and pfm.get("Status") == "🟢 complete":
                pco = company_of(pfm)
                if pco and pco in active_project_companies:
                    actives = active_project_by_company.get(pco, [])
                    # --fix re-points, but only when the active engagement is
                    # unambiguous (exactly one) — else surface it for a human.
                    if args.fix and len(actives) == 1:
                        tpath = f"Tasks/{tbase}.md"
                        ttext = open(tpath, encoding="utf-8").read()
                        new = re.sub(
                            rf'(?m)^(Project:\s*").*?(")\s*$',
                            rf'\g<1>[[{actives[0]}]]\g<2>', ttext, count=1)
                        if new != ttext:
                            open(tpath, "w", encoding="utf-8", newline="\n").write(new)
                            fixed += 1
                            continue
                    hint = (f"[[{actives[0]}]]" if len(actives) == 1
                            else "the active engagement (ambiguous — >1 active)")
                    warnings.append((f"Tasks/{tbase}.md",
                                     f"P8: open task points at completed engagement "
                                     f"[[{ptgt}]] while [[{pco}]] has an active one "
                                     f"(renewal orphan) — --fix re-points to {hint}"))

    # =============================== GRAPH PASS (G3) ===============================
    # inbound-reference set across every note body + frontmatter in the vault
    referenced = set()
    for p in glob.glob("**/*.md", recursive=True):
        pp = p.replace("\\", "/")
        if ".obsidian" in pp or pp.startswith("Administrator"):
            continue
        try:
            t = open(p, encoding="utf-8").read()
        except Exception:
            continue
        self_base = os.path.splitext(os.path.basename(p))[0]
        for tgt in re.findall(r'\[\[([^\]|#]+)', t):
            tgt = tgt.strip()
            if tgt and tgt != self_base:
                referenced.add(tgt)
    # G3: orphan synthesis pages (no inbound links) in Notes/ and Cowork/os/knowledge/
    for root in ("Notes", "Cowork/os/knowledge"):
        for p in glob.glob(os.path.join(root, "**", "*.md"), recursive=True):
            pp = p.replace("\\", "/")
            if pp.startswith("Notes/Archive/Notion Migration/"):
                continue
            b = os.path.splitext(os.path.basename(p))[0]
            if b not in referenced and b.lower() not in ("index", "readme"):
                warnings.append((pp, "G3: orphan page (no inbound wikilinks)"))

    # ---- bridge checks (Cowork <-> vault) ----
    clients_root = os.path.join("Cowork", "clients")
    if os.path.isdir(clients_root):
        folders = sorted(
            d for d in os.listdir(clients_root)
            if os.path.isdir(os.path.join(clients_root, d))
            and d != "_template" and not d.startswith(".")
        )
        folder_set = set(folders)
        for rel, cw in cowork_refs:
            if cw not in folder_set:
                errors.append((rel, f"cowork_client: {cw!r} has no Cowork/clients/{cw}/ folder"))
        ptr_re = re.compile(r"\*\*TARS project:\*\*\s*(.+?)\s*(?:·.*)?$", re.M)
        cpr_re = re.compile(r"\*\*TARS company:\*\*\s*(.+?)\s*$", re.M)
        for folder in folders:
            frel = f"Cowork/clients/{folder}/CLAUDE.md"
            comps = company_by_client.get(folder, [])
            if not comps:
                errors.append((frel, f"client folder has no CRM company note "
                                     f"(no crm_company with cowork_client: {folder!r})"))
            elif len(comps) > 1:
                errors.append((frel, f"multiple company notes claim cowork_client {folder!r}: {comps}"))
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
                tgt = re.sub(r"\s*_?\(.*$", "", tgt).strip()
                if tgt and tgt not in all_notes:
                    errors.append((frel, f"**TARS company:** -> {tgt!r} resolves to no note"))

    # ---- PM write-through drift check (P5) ----
    try:
        gitlog = subprocess.run(
            ["git", "log", "--since=7.days", "--name-only",
             "--pretty=format:@%ad%x1f%s", "--date=short"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        ).stdout
    except Exception:
        gitlog = ""
    ws_days = set()
    for f in glob.glob(os.path.join("Work Sessions", "*.md")):
        m = re.match(r"^(.+) - WS (\d{4}-\d{2}-\d{2})",
                     os.path.splitext(os.path.basename(f))[0])
        if m:
            ws_days.add((m.group(1), m.group(2)))
    BULK_THRESHOLD = 3
    commits, cur = [], None
    for ln in gitlog.splitlines():
        if ln.startswith("@"):
            header = ln[1:].split("\x1f", 1)
            cur = {
                "day": header[0].strip(),
                "subject": header[1].strip() if len(header) == 2 else "",
                "clients": set(),
            }
            commits.append(cur)
            continue
        m = re.match(r"^Cowork/clients/([^/]+)/", ln.strip().replace("\\", "/"))
        if m and cur is not None and m.group(1) != "_template":
            cur["clients"].add(m.group(1))
    touched = set()
    for c in commits:
        if p5_subject_is_delivery(c["subject"]) and 0 < len(c["clients"]) <= BULK_THRESHOLD:
            touched.update((cl, c["day"]) for cl in c["clients"])
    live_clients = {d for d in os.listdir(clients_root)
                    if os.path.isdir(os.path.join(clients_root, d))
                    and not d.startswith(".")} \
        if os.path.isdir(clients_root) else set()
    for client, day in sorted(touched):
        if client not in live_clients:
            continue
        if (client, day) not in ws_days:
            warnings.append((f"Cowork/clients/{client}/",
                             f"P5: commit on {day} touched this client but no "
                             f"'Work Sessions/{client} - WS {day} *' note exists "
                             f"(PM write-through missed — log it with /ws)"))

    # ---- machine identity check ----
    mfile = os.path.join("Cowork", ".ai-os-machine")
    if os.path.isfile(mfile):
        label = open(mfile, encoding="utf-8").read().strip()
        valid = ENUMS["task"]["Executor"]
        if label not in valid:
            errors.append(("Cowork/.ai-os-machine",
                           f"machine label {label!r} is not a valid Executor value "
                           f"{sorted(valid)} — /catchup task routing will silently match nothing"))

    # ---- report ----
    print(f"TARS unified lint — {n_notes} notes · schema + propagation + graph · today={today}\n")
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
