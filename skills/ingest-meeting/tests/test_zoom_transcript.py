from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "zoom_transcript.py"
SPEC = importlib.util.spec_from_file_location("zoom_transcript", MODULE_PATH)
assert SPEC and SPEC.loader
zoom_transcript = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = zoom_transcript
SPEC.loader.exec_module(zoom_transcript)


UUID_A = "Qsxurc+oRsCOC8fTu197rA=="
UUID_B = "fnMXkA+NTGKU8w1QptzdWQ=="
UUID_C = "cTIbfkLQRAOGqKUtvpcCdw=="


def recording(uuid, number, start, end, transcript=True, topic="Acme <> Datarails | Sync"):
    """One recordings_list meeting, shaped like the Zoom connector output."""
    files = [{"file_type": "MP4", "status": "completed",
              "recording_start": start, "recording_end": end}]
    if transcript:
        files.append({"file_type": "TRANSCRIPT", "status": "completed",
                      "recording_start": start, "recording_end": end})
    return {"uuid": uuid, "id": number, "topic": topic, "start_time": start,
            "recording_files": files}


class ZoomTranscriptTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)
        (self.vault / "Meetings").mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_meeting(self, name="Acme - Sync (2026-10-01)", start="2026-10-01 10:15",
                      end="2026-10-01 10:47", call_url=None, zoom_uuid=None,
                      gong_title="Acme <> Datarails | Sync") -> Path:
        lines = ["---", "fileClass: meeting"]
        if gong_title:
            lines.append(f'GongTitle: "{gong_title}"')
        if call_url:
            lines.append(f'CallUrl: "{call_url}"')
        if start:
            lines.append(f"StartTime: {start}")
        if end:
            lines.append(f"EndTime: {end}")
        if zoom_uuid:
            lines.append(f'ZoomMeetingUUID: "{zoom_uuid}"')
        lines += ["---", "", "## Recap", "", "## Key Points", "", "## Next Steps", ""]
        path = self.vault / "Meetings" / f"{name}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def write_json(self, name: str, payload: dict) -> Path:
        path = self.vault / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def match(self, meeting: Path, meetings: list | None) -> dict:
        recordings = None
        if meetings is not None:
            recordings = self.write_json("recordings.json", {"meetings": meetings})
        return zoom_transcript.match(meeting, recordings)


class MatchTests(ZoomTranscriptTestCase):
    # Meeting 10:15-10:47 America/Edmonton (MDT) = 16:15-16:47Z.

    def test_one_transcript_recording_matches(self):
        result = self.match(self.write_meeting(), [
            recording(UUID_A, 897, "2026-10-01T16:19:01Z", "2026-10-01T16:47:23Z"),
        ])
        self.assertEqual(result["status"], "match")
        self.assertEqual(result["uuid"], UUID_A)
        self.assertEqual(result["recording_start"], "2026-10-01 10:19")

    def test_stub_without_transcript_and_adjacent_call_are_ignored(self):
        # The observed shape: a 4-minute false start with no transcript, and a
        # different call that ended just as this one began.
        result = self.match(self.write_meeting(), [
            recording(UUID_B, 897, "2026-10-01T16:14:43Z", "2026-10-01T16:18:43Z",
                      transcript=False),
            recording(UUID_A, 897, "2026-10-01T16:19:01Z", "2026-10-01T16:47:23Z"),
            recording(UUID_C, 812, "2026-10-01T16:00:38Z", "2026-10-01T16:19:38Z",
                      topic="Debrief"),
        ])
        self.assertEqual((result["status"], result["uuid"]), ("match", UUID_A))

    def test_sub_three_minute_transcript_stub_is_ignored(self):
        result = self.match(self.write_meeting(), [
            recording(UUID_B, 897, "2026-10-01T16:15:00Z", "2026-10-01T16:16:30Z"),
            recording(UUID_A, 897, "2026-10-01T16:17:00Z", "2026-10-01T16:47:00Z"),
        ])
        self.assertEqual((result["status"], result["uuid"]), ("match", UUID_A))

    def test_split_call_falls_back(self):
        result = self.match(self.write_meeting(), [
            recording(UUID_B, 897, "2026-10-01T16:15:00Z", "2026-10-01T16:28:00Z"),
            recording(UUID_A, 897, "2026-10-01T16:30:00Z", "2026-10-01T16:47:00Z"),
        ])
        self.assertEqual((result["status"], result["reason"]), ("fallback", "split-recording"))

    def test_partial_recording_falls_back(self):
        result = self.match(self.write_meeting(), [
            recording(UUID_A, 897, "2026-10-01T16:35:00Z", "2026-10-01T16:47:00Z"),
        ])
        self.assertEqual((result["status"], result["reason"]), ("fallback", "partial-recording"))

    def test_no_recording_falls_back(self):
        result = self.match(self.write_meeting(), [
            recording(UUID_C, 812, "2026-10-01T14:00:00Z", "2026-10-01T14:30:00Z"),
        ])
        self.assertEqual((result["status"], result["reason"]), ("fallback", "no-recording"))

    def test_overlapping_call_with_another_title_is_not_matched(self):
        # Observed 2026-09-30: Gong recorded a TAM meeting Patrick did not host while
        # his own Zoom recorded an overlapping review. Time alone matched both.
        meeting = self.write_meeting(gong_title="TAM Team Weekly Meeting")
        result = self.match(meeting, [
            recording(UUID_A, 897, "2026-10-01T16:15:00Z", "2026-10-01T16:47:00Z",
                      topic="Patrick / Riley -- Report Review"),
        ])
        self.assertEqual((result["status"], result["reason"]), ("fallback", "no-recording"))

    def test_title_match_ignores_case_and_spacing(self):
        meeting = self.write_meeting(gong_title="acme <>  Datarails | sync")
        result = self.match(meeting, [
            recording(UUID_A, 897, "2026-10-01T16:15:00Z", "2026-10-01T16:47:00Z"),
        ])
        self.assertEqual(result["status"], "match")

    def test_meeting_without_title_or_zoom_number_falls_back(self):
        result = self.match(self.write_meeting(gong_title=None), [
            recording(UUID_A, 897, "2026-10-01T16:15:00Z", "2026-10-01T16:47:00Z"),
        ])
        self.assertEqual((result["status"], result["reason"]), ("fallback", "no-identity"))

    def test_zoom_call_url_restricts_to_its_meeting_number(self):
        meeting = self.write_meeting(call_url="https://datarails.zoom.us/j/897?pwd=x",
                                     gong_title=None)
        result = self.match(meeting, [
            recording(UUID_C, 812, "2026-10-01T16:15:00Z", "2026-10-01T16:47:00Z"),
            recording(UUID_A, 897, "2026-10-01T16:16:00Z", "2026-10-01T16:47:00Z"),
        ])
        self.assertEqual((result["status"], result["uuid"]), ("match", UUID_A))

    def test_meeting_without_timing_falls_back(self):
        result = self.match(self.write_meeting(start=None, end=None), [])
        self.assertEqual((result["status"], result["reason"]), ("fallback", "no-timing"))

    def test_already_sourced_meeting_needs_no_recordings(self):
        result = self.match(self.write_meeting(zoom_uuid=UUID_A), None)
        self.assertEqual((result["status"], result["uuid"]), ("sourced", UUID_A))

    def test_missing_recordings_input_is_an_error(self):
        with self.assertRaises(zoom_transcript.TranscriptError):
            self.match(self.write_meeting(), None)


class SlimInputTests(ZoomTranscriptTestCase):
    """Inline connector results are copied as slim input, not retyped verbatim."""

    def run_cli(self, *args: str) -> tuple[int, dict | None]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = zoom_transcript.main(["--vault", str(self.vault), *args])
        text = out.getvalue().strip()
        return code, json.loads(text) if text else None

    def test_match_reads_slim_recording_rows(self):
        meeting = self.write_meeting()
        rows = self.vault / "rows.json"
        rows.write_text(json.dumps([
            {"uuid": UUID_B, "id": 897, "topic": "Acme <> Datarails | Sync",
             "start": "2026-10-01T16:14:43Z", "end": "2026-10-01T16:18:43Z",
             "transcript": False},
            {"uuid": UUID_A, "id": 897, "topic": "Acme <> Datarails | Sync",
             "start": "2026-10-01T16:19:01Z", "end": "2026-10-01T16:47:23Z",
             "transcript": True},
        ]), encoding="utf-8")
        code, result = self.run_cli("match", "--meeting", str(meeting), "--recordings", str(rows))
        self.assertEqual(code, 0)
        self.assertEqual((result["status"], result["uuid"]), ("match", UUID_A))

    def test_render_reads_timeline_lines(self):
        meeting = self.write_meeting()
        lines = self.vault / "timeline.txt"
        lines.write_text(
            "[00:00:36] Patrick Bowyer: Hey, Riley.\n"
            "\n"
            "[00:00:40] Riley Novak: Hey, Patrick.\n"
            "[00:00:42] Riley Novak: How's it going?\n",
            encoding="utf-8",
        )
        code, summary = self.run_cli("render", "--meeting", str(meeting),
                                     "--resource", str(lines), "--uuid", UUID_A)
        self.assertEqual(code, 0)
        self.assertEqual(summary["turns"], 2)
        text = (self.vault / "Transcripts" / f"{meeting.stem}.md").read_text(encoding="utf-8")
        self.assertIn("**[00:00:36] Patrick Bowyer:** Hey, Riley.", text)
        self.assertIn("**[00:00:40] Riley Novak:** Hey, Patrick. How's it going?", text)

    def test_malformed_slim_row_exits_2(self):
        meeting = self.write_meeting()
        rows = self.vault / "rows.json"
        rows.write_text(json.dumps([{"uuid": UUID_A, "topic": "Acme <> Datarails | Sync"}]),
                        encoding="utf-8")
        code, result = self.run_cli("match", "--meeting", str(meeting), "--recordings", str(rows))
        self.assertEqual((code, result), (2, None))

    def test_malformed_recording_timestamp_exits_2(self):
        meeting = self.write_meeting()
        recordings = self.write_json("recordings.json", {"meetings": [
            recording(UUID_A, 897, "2026-10-01 bad", "2026-10-01T16:47:23Z"),
        ]})
        code, result = self.run_cli("match", "--meeting", str(meeting),
                                    "--recordings", str(recordings))
        self.assertEqual((code, result), (2, None))

    def test_recording_timestamp_without_offset_exits_2(self):
        meeting = self.write_meeting()
        recordings = self.write_json("recordings.json", {"meetings": [
            recording(UUID_A, 897, "2026-10-01T16:19:01", "2026-10-01T16:47:23"),
        ]})
        code, result = self.run_cli("match", "--meeting", str(meeting),
                                    "--recordings", str(recordings))
        self.assertEqual((code, result), (2, None))

    def test_matched_recording_without_uuid_exits_2(self):
        meeting = self.write_meeting()
        missing = recording(UUID_A, 897, "2026-10-01T16:19:01Z", "2026-10-01T16:47:23Z")
        del missing["uuid"]
        recordings = self.write_json("recordings.json", {"meetings": [missing]})
        code, result = self.run_cli("match", "--meeting", str(meeting),
                                    "--recordings", str(recordings))
        self.assertEqual((code, result), (2, None))

    def test_malformed_timeline_line_exits_2(self):
        meeting = self.write_meeting()
        lines = self.vault / "timeline.txt"
        lines.write_text("Patrick Bowyer said hello\n", encoding="utf-8")
        code, result = self.run_cli("render", "--meeting", str(meeting),
                                    "--resource", str(lines), "--uuid", UUID_A)
        self.assertEqual((code, result), (2, None))
        self.assertFalse((self.vault / "Transcripts").exists())


class RenderTests(ZoomTranscriptTestCase):
    def resource(self, *clips) -> Path:
        return self.write_json("resource.json", {"transcripts": [
            {"recording_start": start, "timeline": [
                {"ts": ts, "display_name": who, "text": text, "avatar": "https://x"}
                for ts, who, text in timeline
            ]} for start, timeline in clips
        ]})

    def test_writes_turns_merged_by_speaker(self):
        meeting = self.write_meeting()
        resource = self.resource((1791232213000, [
            ("00:00:36.720", "Patrick Bowyer", "Hey, Riley."),
            ("00:00:40.820", "Riley Novak", "Hey, Patrick."),
            ("00:00:42.100", "Riley Novak", "How's it going?"),
        ]))
        summary = zoom_transcript.render(self.vault, meeting, resource, UUID_A)
        text = (self.vault / "Transcripts" / f"{meeting.stem}.md").read_text(encoding="utf-8")
        self.assertIn(f'Meeting: "[[{meeting.stem}]]"', text)
        self.assertIn(f'ZoomMeetingUUID: "{UUID_A}"', text)
        self.assertIn("**[00:00:36] Patrick Bowyer:** Hey, Riley.", text)
        self.assertIn("**[00:00:40] Riley Novak:** Hey, Patrick. How's it going?", text)
        self.assertNotIn("avatar", text)
        self.assertEqual(summary["turns"], 2)
        self.assertEqual(summary["speakers"], ["Patrick Bowyer", "Riley Novak"])

    def test_speaker_names_are_escaped_in_frontmatter(self):
        meeting = self.write_meeting()
        resource = self.resource((1000, [
            ("00:00:01.000", 'Pat "PB" Bowyer', "hello"),
            ("00:00:02.000", "DOMAIN\\amy", "hi"),
        ]))
        zoom_transcript.render(self.vault, meeting, resource, UUID_A)
        text = (self.vault / "Transcripts" / f"{meeting.stem}.md").read_text(encoding="utf-8")
        self.assertIn('  - "Pat \\"PB\\" Bowyer"\n', text)
        self.assertIn('  - "DOMAIN\\\\amy"\n', text)

    def test_clips_are_concatenated_in_start_order(self):
        meeting = self.write_meeting()
        resource = self.resource(
            (2000, [("00:00:01.000", "B", "second clip")]),
            (1000, [("00:00:01.000", "A", "first clip")]),
        )
        zoom_transcript.render(self.vault, meeting, resource, UUID_A)
        text = (self.vault / "Transcripts" / f"{meeting.stem}.md").read_text(encoding="utf-8")
        self.assertLess(text.index("first clip"), text.index("## Clip 2"))
        self.assertLess(text.index("## Clip 2"), text.index("second clip"))

    def test_rerender_is_byte_identical(self):
        meeting = self.write_meeting()
        resource = self.resource((1000, [("00:00:01.000", "A", "hello")]))
        zoom_transcript.render(self.vault, meeting, resource, UUID_A)
        path = self.vault / "Transcripts" / f"{meeting.stem}.md"
        first = path.read_bytes()
        summary = zoom_transcript.render(self.vault, meeting, resource, UUID_A)
        self.assertEqual(path.read_bytes(), first)
        self.assertFalse(summary["changed"])

    def test_empty_transcript_is_an_error(self):
        meeting = self.write_meeting()
        with self.assertRaises(zoom_transcript.TranscriptError):
            zoom_transcript.render(self.vault, meeting, self.resource(), UUID_A)

    def test_meeting_number_is_not_a_uuid(self):
        meeting = self.write_meeting()
        resource = self.resource((1000, [("00:00:01.000", "A", "hello")]))
        with self.assertRaises(zoom_transcript.TranscriptError):
            zoom_transcript.render(self.vault, meeting, resource, "82317898892")


if __name__ == "__main__":
    unittest.main()
