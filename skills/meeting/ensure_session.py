#!/usr/bin/env python3
"""Ensure one authoritative Work Session exists for a Meeting source.

The Meeting supplies immutable source timing.  Once a Work Session exists, its
ledger timing is never rewritten: timing disagreement is reported as an exception.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_.-]*):(?:[ \t]*(.*))?$")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
LIVE_ACTIVITY_TYPE = "Meeting"
DELETION_CANDIDATE_TAG = "duplicate/meeting-source"


class EnsureSessionError(RuntimeError):
    """A source ambiguity or invalid Meeting prevents safe ledger creation."""


@dataclass(frozen=True)
class Note:
    path: Path
    text: str
    frontmatter: dict[str, str]
    body: str


@dataclass(frozen=True)
class EnsureResult:
    action: str
    session_path: Path
    warnings: tuple[str, ...] = ()


def _split_frontmatter(text: str, path: Path) -> tuple[list[str], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise EnsureSessionError(f"{path}: missing YAML frontmatter")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index], "".join(lines[index + 1 :])
    raise EnsureSessionError(f"{path}: unterminated YAML frontmatter")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    if value in {"null", "~"}:
        return ""
    return value


def _read_note(path: Path) -> Note:
    text = path.read_text(encoding="utf-8")
    fm_lines, body = _split_frontmatter(text, path)
    frontmatter: dict[str, str] = {}
    for line in fm_lines:
        if line.startswith((" ", "\t")):
            continue
        match = KEY_RE.match(line.rstrip("\r\n"))
        if match:
            frontmatter[match.group(1)] = _unquote(match.group(2) or "")
    return Note(path=path, text=text, frontmatter=frontmatter, body=body)


def _link_target(value: str) -> str:
    match = LINK_RE.search(value or "")
    if not match:
        return ""
    return Path(match.group(1).strip()).name


def _related_call_target(body: str) -> str:
    for line in body.splitlines():
        if line.lower().startswith("related call:"):
            return _link_target(line)
    return ""


def _has_frontmatter_tag(note: Note, tag: str) -> bool:
    fm_lines, _ = _split_frontmatter(note.text, note.path)
    in_tags = False
    for raw_line in fm_lines:
        line = raw_line.rstrip("\r\n")
        key_match = KEY_RE.match(line)
        if key_match:
            in_tags = key_match.group(1) == "tags"
            if in_tags:
                inline = key_match.group(2) or ""
                values = [part.strip(" \t[]\"'") for part in inline.split(",")]
                if tag in values:
                    return True
            continue
        if in_tags and line.startswith((" ", "\t")):
            value = line.strip()
            if value.startswith("-") and value[1:].strip(" \t\"'") == tag:
                return True
        elif line.strip():
            in_tags = False
    return False


def _quote_link(target: str) -> str:
    return f'"[[{target}]]"'


def _replace_or_add_scalar(text: str, key: str, value: str) -> str:
    lines = text.splitlines(keepends=True)
    closing = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing = index
            break
        match = KEY_RE.match(lines[index].rstrip("\r\n"))
        if match and match.group(1) == key:
            newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
            lines[index] = f"{key}: {value}{newline}"
            return "".join(lines)
    if closing is None:
        raise EnsureSessionError("cannot update unterminated frontmatter")
    newline = "\r\n" if lines[0].endswith("\r\n") else "\n"
    lines.insert(closing, f"{key}: {value}{newline}")
    return "".join(lines)


def _write_if_unchanged(path: Path, old_text: str, new_text: str) -> None:
    if old_text == new_text:
        return
    if path.read_text(encoding="utf-8") != old_text:
        raise EnsureSessionError(f"{path}: changed concurrently; re-run safely")
    temporary = path.with_name(f".{path.name}.ensure-session-{os.getpid()}")
    try:
        temporary.write_text(new_text, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _resolve_meeting(vault: Path, value: str) -> Path:
    supplied = Path(value)
    candidates: list[Path] = []
    if supplied.is_absolute() and supplied.is_file():
        candidates = [supplied]
    elif (vault / supplied).is_file():
        candidates = [vault / supplied]
    else:
        stem = supplied.stem.casefold()
        candidates = [
            path
            for path in (vault / "Meetings").rglob("*.md")
            if path.stem.casefold() == stem
        ]
    candidates = sorted({path.resolve() for path in candidates})
    if not candidates:
        raise EnsureSessionError(f"Meeting not found: {value}")
    if len(candidates) > 1:
        joined = ", ".join(str(path) for path in candidates)
        raise EnsureSessionError(f"Meeting reference is ambiguous: {joined}")
    meetings_root = (vault / "Meetings").resolve()
    try:
        candidates[0].relative_to(meetings_root)
    except ValueError as exc:
        raise EnsureSessionError(f"Meeting must be inside {meetings_root}") from exc
    return candidates[0]


def _resolve_project(vault: Path, target: str) -> Note:
    if not target:
        raise EnsureSessionError("Meeting.Project is required before ledger creation")
    matches = [
        path
        for path in (vault / "Projects").rglob("*.md")
        if path.stem == target
    ]
    if not matches:
        raise EnsureSessionError(f"Meeting.Project does not resolve: [[{target}]]")
    if len(matches) > 1:
        raise EnsureSessionError(f"Meeting.Project is ambiguous: [[{target}]]")
    return _read_note(matches[0])


def _derive_identity(meeting: Note, project: Note) -> tuple[str, str, str]:
    project_name = project.path.stem
    project_company = _link_target(project.frontmatter.get("Company", ""))
    meeting_company = _link_target(meeting.frontmatter.get("Company", ""))
    lowered = project_name.casefold()

    if project_name == "Datarails Ongoing":
        bucket = "Internal Operations"
    elif "tars" in lowered or "unified os" in lowered:
        bucket = "TARS / OS"
    elif project_company:
        bucket = "Client Delivery"
    else:
        raise EnsureSessionError(
            f"Project [[{project_name}]] has no classifiable reporting identity"
        )

    if meeting_company and project_company and meeting_company != project_company:
        raise EnsureSessionError(
            f"Meeting.Company [[{meeting_company}]] conflicts with "
            f"Project.Company [[{project_company}]]"
        )
    company = project_company or meeting_company
    if bucket == "Client Delivery" and not company:
        raise EnsureSessionError(
            f"Client Delivery project [[{project_name}]] must resolve a Company"
        )
    return project_name, company, bucket


def _parse_time(note: Note, key: str) -> datetime:
    raw = note.frontmatter.get(key, "")
    if not raw:
        raise EnsureSessionError(f"{note.path.name}: {key} is required to seed a session")
    try:
        return datetime.strptime(raw, DATETIME_FORMAT)
    except ValueError as exc:
        raise EnsureSessionError(
            f"{note.path.name}: {key} must be YYYY-MM-DD HH:mm, got {raw!r}"
        ) from exc


def _meeting_gong_ids(vault: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in (vault / "Meetings").rglob("*.md"):
        try:
            note = _read_note(path)
        except (OSError, UnicodeError, EnsureSessionError):
            continue
        gong_id = note.frontmatter.get("GongId", "").strip()
        if gong_id:
            result[path.stem] = gong_id
    return result


def _session_notes(vault: Path) -> Iterable[Note]:
    for path in sorted((vault / "Work Sessions").rglob("*.md")):
        try:
            note = _read_note(path)
        except (OSError, UnicodeError, EnsureSessionError):
            continue
        if (
            note.frontmatter.get("fileClass") == "session"
            and not _has_frontmatter_tag(note, DELETION_CANDIDATE_TAG)
        ):
            yield note


def _is_live_call_session(session: Note) -> bool:
    """Exclude prep/follow-up task sessions that merely reference the Meeting."""
    return session.frontmatter.get("ActivityType", "") == LIVE_ACTIVITY_TYPE


def _same_dimensions(
    session: Note, project_name: str, company: str, start_raw: str, end_raw: str
) -> bool:
    return (
        _link_target(session.frontmatter.get("Project", "")) == project_name
        and _link_target(session.frontmatter.get("Company", "")) == company
        and session.frontmatter.get("StartTime", "") == start_raw
        and session.frontmatter.get("EndTime", "") == end_raw
        and session.frontmatter.get("ActivityType", "") == LIVE_ACTIVITY_TYPE
    )


def _find_candidates(
    vault: Path,
    meeting: Note,
    project_name: str,
    company: str,
) -> tuple[list[Note], str]:
    meeting_name = meeting.path.stem
    gong_id = meeting.frontmatter.get("GongId", "").strip()
    gong_ids = _meeting_gong_ids(vault) if gong_id else {}
    sessions = list(_session_notes(vault))

    primary: list[Note] = []
    for session in sessions:
        if not _is_live_call_session(session):
            continue
        linked = _link_target(session.frontmatter.get("Meeting", ""))
        related = _related_call_target(session.body)
        if linked == meeting_name or related == meeting_name:
            primary.append(session)
        elif gong_id and (linked or related) and gong_ids.get(linked or related) == gong_id:
            primary.append(session)
    if primary:
        return primary, "source identity"

    # A timing/dimension fallback is deliberately limited to non-Gong meetings.
    # Gong sources must match by their stable ID or an explicit Meeting reference.
    if gong_id:
        return [], "Gong identity"
    start_raw = meeting.frontmatter.get("StartTime", "")
    end_raw = meeting.frontmatter.get("EndTime", "")
    fallback = [
        session
        for session in sessions
        if _same_dimensions(session, project_name, company, start_raw, end_raw)
    ]
    return fallback, "non-Gong timing fallback"


def _relative(path: Path, vault: Path) -> str:
    try:
        return str(path.relative_to(vault))
    except ValueError:
        return str(path)


def _validate_existing_dimensions(
    session: Note, project_name: str, company: str, bucket: str
) -> None:
    checks = (
        ("Project", _link_target(session.frontmatter.get("Project", "")), project_name),
        ("Company", _link_target(session.frontmatter.get("Company", "")), company),
        ("ReportingBucket", session.frontmatter.get("ReportingBucket", ""), bucket),
    )
    for field, actual, expected in checks:
        if actual and actual != expected:
            raise EnsureSessionError(
                f"{session.path.name}: {field} {actual!r} conflicts with derived {expected!r}"
            )


def _reuse_session(
    session: Note,
    meeting: Note,
    project_name: str,
    company: str,
    bucket: str,
    vault: Path,
) -> EnsureResult:
    _validate_existing_dimensions(session, project_name, company, bucket)
    updated = session.text
    linked = _link_target(session.frontmatter.get("Meeting", ""))
    if not linked:
        updated = _replace_or_add_scalar(updated, "Meeting", _quote_link(meeting.path.stem))
    if not session.frontmatter.get("ReportingBucket", ""):
        updated = _replace_or_add_scalar(updated, "ReportingBucket", bucket)
    _write_if_unchanged(session.path, session.text, updated)

    warnings: list[str] = []
    start = meeting.frontmatter.get("StartTime", "")
    end = meeting.frontmatter.get("EndTime", "")
    ledger_start = session.frontmatter.get("StartTime", "")
    ledger_end = session.frontmatter.get("EndTime", "")
    if not start:
        warnings.append("source timing exception: Meeting.StartTime is missing")
    elif ledger_start and start != ledger_start:
        warnings.append(
            f"timing exception: Meeting.StartTime {start} != ledger StartTime {ledger_start}"
        )
    if not end:
        warnings.append("source timing exception: Meeting.EndTime is missing")
    elif ledger_end and end != ledger_end:
        warnings.append(
            f"timing exception: Meeting.EndTime {end} != ledger EndTime {ledger_end}"
        )
    return EnsureResult("reused", session.path, tuple(warnings))


def _safe_prefix(company: str, project_name: str, bucket: str) -> str:
    if company:
        prefix = company
    elif bucket == "Internal Operations":
        prefix = "Datarails"
    elif bucket == "TARS / OS":
        prefix = "TARS"
    else:
        prefix = project_name
    return re.sub(r"[\\/:*?\"<>|]", "-", prefix).strip() or "Session"


def _new_session_path(
    vault: Path, company: str, project_name: str, bucket: str, start: datetime
) -> Path:
    directory = vault / "Work Sessions"
    directory.mkdir(parents=True, exist_ok=True)
    prefix = _safe_prefix(company, project_name, bucket)
    base = f"{prefix} - WS {start:%Y-%m-%d %H%M}"
    candidate = directory / f"{base}.md"
    suffix = 2
    while candidate.exists():
        candidate = directory / f"{base} ({suffix}).md"
        suffix += 1
    return candidate


def _session_text(
    meeting: Note,
    project_name: str,
    company: str,
    bucket: str,
    start: datetime,
    end: datetime,
) -> str:
    duration = int((end - start).total_seconds() // 60)
    hours_type = "Billable" if bucket == "Client Delivery" else "Non-billable"
    audience = "External" if bucket == "Client Delivery" else "Internal"
    modified = datetime.now().astimezone().replace(microsecond=0).isoformat()
    company_line = f"Company: {_quote_link(company)}\n" if company else "Company:\n"
    return (
        "---\n"
        "fileClass: session\n"
        "Task:\n"
        f"Meeting: {_quote_link(meeting.path.stem)}\n"
        f"Project: {_quote_link(project_name)}\n"
        f"{company_line}"
        f"ReportingBucket: {bucket}\n"
        f"HoursType: {hours_type}\n"
        "ActivityType: Meeting\n"
        f"Audience: {audience}\n"
        f"StartTime: {start:{DATETIME_FORMAT}}\n"
        f"EndTime: {end:{DATETIME_FORMAT}}\n"
        f"DurationMin: {duration}\n"
        "ReclaimEventID:\n"
        "tags:\n"
        "  - session\n"
        f"modified: {modified}\n"
        "---\n"
    )


def ensure_session(vault: Path, meeting_value: str, dry_run: bool = False) -> EnsureResult:
    vault = vault.resolve()
    meeting_path = _resolve_meeting(vault, meeting_value)
    meeting = _read_note(meeting_path)
    if meeting.frontmatter.get("fileClass") != "meeting":
        raise EnsureSessionError(f"{meeting.path}: fileClass must be meeting")

    project_target = _link_target(meeting.frontmatter.get("Project", ""))
    project = _resolve_project(vault, project_target)
    project_name, company, bucket = _derive_identity(meeting, project)
    meeting_bucket = meeting.frontmatter.get("ReportingBucket", "")
    if meeting_bucket and meeting_bucket != bucket:
        raise EnsureSessionError(
            f"{meeting.path.name}: ReportingBucket {meeting_bucket!r} conflicts "
            f"with project-derived {bucket!r}"
        )

    candidates, match_kind = _find_candidates(
        vault, meeting, project_name, company
    )
    unique = {candidate.path.resolve(): candidate for candidate in candidates}
    if len(unique) > 1:
        names = ", ".join(_relative(path, vault) for path in sorted(unique))
        raise EnsureSessionError(
            f"{meeting.path.name}: multiple Work Sessions match by {match_kind}: {names}"
        )

    if not meeting_bucket and not dry_run:
        updated_meeting = _replace_or_add_scalar(meeting.text, "ReportingBucket", bucket)
        _write_if_unchanged(meeting.path, meeting.text, updated_meeting)

    if unique:
        session = next(iter(unique.values()))
        if dry_run:
            _validate_existing_dimensions(session, project_name, company, bucket)
            return EnsureResult("would-reuse", session.path)
        return _reuse_session(session, meeting, project_name, company, bucket, vault)

    start = _parse_time(meeting, "StartTime")
    end = _parse_time(meeting, "EndTime")
    if end <= start:
        raise EnsureSessionError(
            f"{meeting.path.name}: EndTime must be later than StartTime"
        )
    if (end - start).total_seconds() % 60:
        raise EnsureSessionError(
            f"{meeting.path.name}: duration must resolve to whole minutes"
        )
    session_path = _new_session_path(vault, company, project_name, bucket, start)
    if dry_run:
        return EnsureResult("would-create", session_path)
    try:
        with session_path.open("x", encoding="utf-8") as handle:
            handle.write(_session_text(meeting, project_name, company, bucket, start, end))
    except FileExistsError as exc:
        raise EnsureSessionError(
            f"{session_path}: appeared concurrently; re-run safely"
        ) from exc
    return EnsureResult("created", session_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("meeting", help="Meeting path or unique Meeting basename")
    parser.add_argument(
        "--vault", type=Path, default=Path.cwd(), help="vault root (default: cwd)"
    )
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = ensure_session(args.vault, args.meeting, args.dry_run)
    except EnsureSessionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"{result.action.upper()}: {_relative(result.session_path, args.vault.resolve())}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
