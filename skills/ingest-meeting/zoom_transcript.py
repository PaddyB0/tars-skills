#!/usr/bin/env python3
"""Match a Meeting note to its Zoom recording and store the raw transcript.

/ingest-meeting fetches through the Zoom connector, which only an agent session
can reach; this script does the deterministic part on the saved JSON.

    match   --meeting <note> [--recordings <recordings_list json>]
    render  --meeting <note> --resource <get_recording_resource json> --uuid <uuid>

`match` prints one JSON object and exits 0:

    {"status": "sourced",  "uuid": ...}   ZoomMeetingUUID already set; reuse it
    {"status": "match",    "uuid": ..., "topic": ..., "recording_start": ...,
                           "duration_min": ...}
    {"status": "fallback", "reason": ..., "detail": ...}

Fallback reasons: `no-timing` (no StartTime/EndTime), `no-identity` (neither a
GongTitle nor a Zoom CallUrl to confirm the recording), `no-recording` (no usable
transcript overlaps the call), `split-recording` (more than one usable transcript
overlaps it), `partial-recording` (the one transcript covers under half the call).

A candidate must carry the Meeting's identity: its Zoom topic equals `GongTitle`
(case and spacing ignored), and a Zoom CallUrl (`/j/<number>`) restricts it to
that meeting number. Time overlap alone is never enough, because Gong records
calls Patrick did not host while his own Zoom records an overlapping one. A
usable transcript is a completed TRANSCRIPT file on a recording of at least
3 minutes. A recording overlaps when the overlap is at least half of the shorter
of the recording and the Meeting.

Each input takes the connector JSON as saved (a file that starts with `{`) or a
slim form for results that came back inline, so the agent copies only what the
script reads:

    --recordings  JSON list of rows, one per recording:
                  {"uuid", "id", "topic", "start", "end", "transcript"}
                  `start`/`end` are the recording's ISO UTC times (the TRANSCRIPT
                  file's when present); `transcript` is true when a completed
                  TRANSCRIPT file exists.
    --resource    One line per timeline entry, `[HH:MM:SS] Speaker: text`, single
                  clip only. Blank lines are skipped; any other line is an error.

`render` writes `Transcripts/<meeting basename>.md` (gitignored): speaker turns,
consecutive lines by one speaker merged, clips in start order. It rewrites the
file only when the content differs and prints a JSON summary.

Exit 2 on unusable input (unreadable note or JSON, a recording timestamp that is
not ISO 8601 with an offset, a matched recording with no uuid, a malformed slim
row or line, an empty transcript, a bad UUID).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_.-]*):(?:[ \t]*(.*))?$")
ZOOM_NUMBER_RE = re.compile(r"zoom\.us/j/(\d+)")
ROW_KEYS = ("uuid", "id", "topic", "start", "end", "transcript")
TIMELINE_LINE_RE =re.compile(r"^\[(\d{1,2}:\d{2}:\d{2})(?:\.\d+)?\]\s+([^:]+?):\s*(.*)$")
ZOOM_UUID_RE = re.compile(
    r"^(?:[A-Za-z0-9+/]{22}==|[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12})$",
    re.I,
)
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
LOCAL_TZ = ZoneInfo("America/Edmonton")
MIN_RECORDING = timedelta(minutes=3)
MIN_OVERLAP_SHARE = 0.5
MIN_COVERAGE = 0.5


class TranscriptError(RuntimeError):
    """The input cannot be matched or rendered safely."""


def _frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise TranscriptError(f"{path}: {exc}") from exc
    if not lines or lines[0].strip() != "---":
        raise TranscriptError(f"{path}: missing YAML frontmatter")
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        found = KEY_RE.match(line)
        if found:
            value = (found.group(2) or "").strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[found.group(1)] = value
    raise TranscriptError(f"{path}: unterminated YAML frontmatter")


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TranscriptError(f"{path}: {exc}") from exc


def _recordings(path: Path) -> list[dict]:
    """Connector `recordings_list` JSON (an object), or slim rows (a list)."""
    data = _load_json(path)
    if isinstance(data, dict):
        return data.get("meetings") or []
    meetings = []
    for number, row in enumerate(data, start=1):
        missing = [k for k in ROW_KEYS if not isinstance(row, dict) or k not in row]
        if missing:
            raise TranscriptError(f"{path}: row {number} lacks {', '.join(missing)}")
        meetings.append({
            "uuid": row["uuid"],
            "id": row["id"],
            "topic": row["topic"],
            "recording_files": [{
                "file_type": "TRANSCRIPT" if row["transcript"] else "MP4",
                "status": "completed",
                "recording_start": row["start"],
                "recording_end": row["end"],
            }],
        })
    return meetings


def _normal(title: str) -> str:
    return " ".join(str(title).split()).casefold()


def _local(moment: datetime) -> str:
    return moment.astimezone(LOCAL_TZ).strftime(DATETIME_FORMAT)


def _utc(value: str) -> datetime:
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise TranscriptError(f"recording timestamp {value!r} is not ISO 8601") from exc
    if moment.tzinfo is None:
        raise TranscriptError(f"recording timestamp {value!r} has no UTC offset")
    return moment


def _span(meeting: dict) -> tuple[datetime, datetime, bool] | None:
    """(start, end, has_transcript) for one recordings_list meeting."""
    files = meeting.get("recording_files") or []
    transcripts = [
        f for f in files
        if f.get("file_type") == "TRANSCRIPT" and f.get("status", "completed") == "completed"
    ]
    timed = transcripts or files
    starts = [f["recording_start"] for f in timed if f.get("recording_start")]
    ends = [f["recording_end"] for f in timed if f.get("recording_end")]
    if not starts or not ends:
        return None
    return _utc(min(starts)), _utc(max(ends)), bool(transcripts)


def match(meeting_path: Path, recordings_path: Path | None) -> dict:
    fm = _frontmatter(meeting_path)
    uuid = fm.get("ZoomMeetingUUID", "")
    if uuid:
        return {"status": "sourced", "uuid": uuid}
    if recordings_path is None:
        raise TranscriptError("--recordings is required until ZoomMeetingUUID is set")
    try:
        start = datetime.strptime(fm.get("StartTime", ""), DATETIME_FORMAT).replace(tzinfo=LOCAL_TZ)
        end = datetime.strptime(fm.get("EndTime", ""), DATETIME_FORMAT).replace(tzinfo=LOCAL_TZ)
    except ValueError:
        return {"status": "fallback", "reason": "no-timing",
                "detail": "Meeting has no StartTime/EndTime"}
    if end <= start:
        return {"status": "fallback", "reason": "no-timing", "detail": "EndTime <= StartTime"}

    number = ZOOM_NUMBER_RE.search(fm.get("CallUrl", ""))
    title = _normal(fm.get("GongTitle", ""))
    if not number and not title:
        return {"status": "fallback", "reason": "no-identity",
                "detail": "no GongTitle or Zoom CallUrl to confirm the recording"}
    meetings = _recordings(recordings_path)
    candidates = []
    for meeting in meetings:
        if number and str(meeting.get("id")) != number.group(1):
            continue
        if title and _normal(meeting.get("topic", "")) != title:
            continue
        span = _span(meeting)
        if span is None:
            continue
        rec_start, rec_end, has_transcript = span
        overlap = min(end, rec_end) - max(start, rec_start)
        shorter = min(end - start, rec_end - rec_start)
        if shorter <= timedelta(0) or overlap / shorter < MIN_OVERLAP_SHARE:
            continue
        if has_transcript and rec_end - rec_start >= MIN_RECORDING:
            candidates.append((meeting, rec_start, rec_end))

    if not candidates:
        return {"status": "fallback", "reason": "no-recording",
                "detail": "no usable Zoom transcript overlaps the Meeting"}
    if len(candidates) > 1:
        return {"status": "fallback", "reason": "split-recording",
                "detail": ", ".join(m.get("uuid", "?") for m, _, _ in candidates)}
    meeting, rec_start, rec_end = candidates[0]
    if not meeting.get("uuid"):
        raise TranscriptError(f"matched recording {meeting.get('topic')!r} has no uuid")
    if (rec_end - rec_start) / (end - start) < MIN_COVERAGE:
        return {"status": "fallback", "reason": "partial-recording",
                "detail": f"{meeting.get('uuid')} covers "
                          f"{int((rec_end - rec_start).total_seconds() // 60)} of "
                          f"{int((end - start).total_seconds() // 60)} min"}
    return {
        "status": "match",
        "uuid": meeting.get("uuid"),
        "topic": meeting.get("topic"),
        "recording_start": _local(rec_start),
        "duration_min": int((rec_end - rec_start).total_seconds() // 60),
    }


def _turns(timeline: list[dict]) -> list[tuple[str, str, str]]:
    turns: list[tuple[str, str, str]] = []
    for line in timeline:
        text = " ".join(str(line.get("text", "")).split())
        if not text:
            continue
        who = str(line.get("display_name") or "Unknown speaker").strip()
        stamp = str(line.get("ts", "")).split(".")[0]
        if turns and turns[-1][1] == who:
            turns[-1] = (turns[-1][0], who, f"{turns[-1][2]} {text}")
        else:
            turns.append((stamp, who, text))
    return turns


def _clips(path: Path) -> list[dict]:
    """Connector `get_recording_resource` JSON (starts with `{`), or timeline lines."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TranscriptError(f"{path}: {exc}") from exc
    if text.lstrip().startswith("{"):
        return _load_json(path).get("transcripts") or []
    timeline = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        found = TIMELINE_LINE_RE.match(line.strip())
        if not found:
            raise TranscriptError(f"{path}:{number}: not `[HH:MM:SS] Speaker: text`")
        stamp, who, said = found.groups()
        timeline.append({"ts": stamp, "display_name": who, "text": said})
    return [{"timeline": timeline}]


def render(vault: Path, meeting_path: Path, resource_path: Path, uuid: str) -> dict:
    if not ZOOM_UUID_RE.fullmatch(uuid.strip()):
        raise TranscriptError(f"{uuid!r} is not a Zoom recording instance UUID")
    _frontmatter(meeting_path)
    clips = sorted(
        (c for c in _clips(resource_path) if c.get("timeline")),
        key=lambda c: c.get("recording_start") or 0,
    )
    clip_turns = [_turns(c["timeline"]) for c in clips]
    if not any(clip_turns):
        raise TranscriptError(f"{resource_path}: transcript is empty")

    speakers: list[str] = []
    for turns in clip_turns:
        for _, who, _ in turns:
            if who not in speakers:
                speakers.append(who)
    started = clips[0].get("recording_start")
    lines = ["---", f'Meeting: "[[{meeting_path.stem}]]"', f'ZoomMeetingUUID: "{uuid.strip()}"']
    if isinstance(started, (int, float)):
        lines.append(f"RecordingStart: {_local(datetime.fromtimestamp(started / 1000, timezone.utc))}")
    lines.append("Speakers:")
    lines += [f"  - {json.dumps(who, ensure_ascii=False)}" for who in speakers]
    lines += ["---", ""]
    for index, turns in enumerate(clip_turns, start=1):
        if len(clip_turns) > 1:
            lines += [f"## Clip {index}", ""]
        for stamp, who, text in turns:
            lines += [f"**[{stamp}] {who}:** {text}", ""]
    content = "\n".join(lines)

    target = vault / "Transcripts" / f"{meeting_path.stem}.md"
    changed = not target.exists() or target.read_text(encoding="utf-8") != content
    if changed:
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(".md.tmp")
        temp.write_text(content, encoding="utf-8", newline="\n")
        temp.replace(target)
    return {
        "path": str(target.relative_to(vault)).replace("\\", "/"),
        "changed": changed,
        "turns": sum(len(t) for t in clip_turns),
        "chars": len(content),
        "speakers": speakers,
    }


def _resolve(vault: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else vault / path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("match", "render"))
    parser.add_argument("--vault", default=".")
    parser.add_argument("--meeting", required=True)
    parser.add_argument("--recordings")
    parser.add_argument("--resource")
    parser.add_argument("--uuid")
    args = parser.parse_args(argv)
    vault = Path(args.vault).resolve()
    meeting = _resolve(vault, args.meeting)
    try:
        if args.command == "match":
            recordings = _resolve(vault, args.recordings) if args.recordings else None
            result = match(meeting, recordings)
        else:
            if not args.resource or not args.uuid:
                raise TranscriptError("render needs --resource and --uuid")
            result = render(vault, meeting, _resolve(vault, args.resource), args.uuid)
    except TranscriptError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
