from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "ensure_session.py"
SPEC = importlib.util.spec_from_file_location("ensure_session", MODULE_PATH)
assert SPEC and SPEC.loader
ensure_session = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ensure_session
SPEC.loader.exec_module(ensure_session)


class EnsureSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)
        for folder in ("Meetings", "Projects", "Work Sessions"):
            (self.vault / folder).mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_project(
        self, name: str = "Acme - CS Hours", company: str = "Acme"
    ) -> Path:
        company_line = f'Company: "[[{company}]]"' if company else "Company:"
        path = self.vault / "Projects" / f"{name}.md"
        path.write_text(
            f"---\nfileClass: project\n{company_line}\ntags: [project]\n---\n",
            encoding="utf-8",
        )
        return path

    def write_meeting(
        self,
        name: str = "Acme - Call (2026-07-15)",
        project: str = "Acme - CS Hours",
        company: str = "Acme",
        gong_id: str = "",
        start: str = "2026-07-15 09:00",
        end: str = "2026-07-15 09:39",
        bucket: str = "Client Delivery",
    ) -> Path:
        company_line = f'Company: "[[{company}]]"' if company else "Company:"
        gong_line = f'GongId: "{gong_id}"' if gong_id else "GongId:"
        end_line = f"EndTime: {end}" if end else "EndTime:"
        bucket_line = f"ReportingBucket: {bucket}\n" if bucket else ""
        path = self.vault / "Meetings" / f"{name}.md"
        path.write_text(
            "---\n"
            "fileClass: meeting\n"
            f"{company_line}\n"
            f'Project: "[[{project}]]"\n'
            f"{bucket_line}"
            "CallType: external call\n"
            f"{gong_line}\n"
            f"StartTime: {start}\n"
            f"{end_line}\n"
            "tags: [meeting]\n"
            "---\n"
            "## Recap\n",
            encoding="utf-8",
        )
        return path

    def write_session(
        self,
        name: str,
        meeting: str = "",
        start: str = "2026-07-15 09:00",
        end: str = "2026-07-15 09:39",
        bucket: str = "Client Delivery",
        activity_type: str = "Meeting",
        audience: str = "External",
        related: str = "",
        deletion_candidate: bool = False,
    ) -> Path:
        meeting_line = f'Meeting: "[[{meeting}]]"\n' if meeting else ""
        bucket_line = f"ReportingBucket: {bucket}\n" if bucket else ""
        deletion_tag = "  - duplicate/meeting-source\n" if deletion_candidate else ""
        path = self.vault / "Work Sessions" / f"{name}.md"
        path.write_text(
            "---\n"
            "fileClass: session\n"
            f"{meeting_line}"
            'Project: "[[Acme - CS Hours]]"\n'
            'Company: "[[Acme]]"\n'
            f"{bucket_line}"
            "HoursType: Billable\n"
            f"ActivityType: {activity_type}\n"
            f"Audience: {audience}\n"
            f"StartTime: {start}\n"
            f"EndTime: {end}\n"
            "DurationMin: 39\n"
            "tags:\n"
            "  - session\n"
            f"{deletion_tag}"
            "---\n"
            f"{related}",
            encoding="utf-8",
        )
        return path

    def test_creates_expected_authoritative_session_and_rerun_reuses_it(self) -> None:
        self.write_project()
        meeting = self.write_meeting()

        first = ensure_session.ensure_session(self.vault, str(meeting))
        self.assertEqual(first.action, "created")
        text = first.session_path.read_text(encoding="utf-8")
        self.assertIn('Meeting: "[[Acme - Call (2026-07-15)]]"', text)
        self.assertIn('Project: "[[Acme - CS Hours]]"', text)
        self.assertIn('Company: "[[Acme]]"', text)
        self.assertIn("ReportingBucket: Client Delivery", text)
        self.assertIn("HoursType: Billable", text)
        self.assertIn("ActivityType: Meeting", text)
        self.assertIn("Audience: External", text)
        self.assertIn("DurationMin: 39", text)

        original = text
        second = ensure_session.ensure_session(self.vault, str(meeting))
        self.assertEqual(second.action, "reused")
        self.assertEqual(second.session_path, first.session_path)
        self.assertEqual(first.session_path.read_text(encoding="utf-8"), original)
        self.assertEqual(len(list((self.vault / "Work Sessions").glob("*.md"))), 1)

    def test_reuses_ledger_timing_without_rewriting_mismatch(self) -> None:
        self.write_project()
        meeting = self.write_meeting()
        session = self.write_session(
            "Acme - WS 2026-07-15 0900",
            meeting=meeting.stem,
            start="2026-07-15 08:55",
            end="2026-07-15 09:45",
        )
        original = session.read_text(encoding="utf-8")

        result = ensure_session.ensure_session(self.vault, meeting.stem)

        self.assertEqual(result.action, "reused")
        self.assertEqual(session.read_text(encoding="utf-8"), original)
        self.assertEqual(len(result.warnings), 2)
        self.assertIn("timing exception", result.warnings[0])

    def test_safe_non_gong_fallback_adds_structured_meeting_link(self) -> None:
        self.write_project()
        meeting = self.write_meeting(gong_id="")
        session = self.write_session("Acme - WS 2026-07-15 0900")

        result = ensure_session.ensure_session(self.vault, meeting.stem)

        self.assertEqual(result.action, "reused")
        self.assertIn(
            f'Meeting: "[[{meeting.stem}]]"', session.read_text(encoding="utf-8")
        )
        self.assertEqual(len(list((self.vault / "Work Sessions").glob("*.md"))), 1)

    def test_prep_session_link_does_not_replace_the_live_call_ledger(self) -> None:
        self.write_project()
        meeting = self.write_meeting(gong_id="gong-123")
        self.write_session(
            "Acme - WS 2026-07-15 0800",
            meeting=meeting.stem,
            start="2026-07-15 08:00",
            end="2026-07-15 08:30",
            activity_type="Build",
        )

        result = ensure_session.ensure_session(self.vault, meeting.stem)

        self.assertEqual(result.action, "created")
        self.assertIn("ActivityType: Meeting", result.session_path.read_text(encoding="utf-8"))
        self.assertEqual(len(list((self.vault / "Work Sessions").glob("*.md"))), 2)

    def test_flagged_import_duplicate_cannot_be_reused_as_authoritative(self) -> None:
        self.write_project()
        meeting = self.write_meeting(gong_id="gong-123")
        duplicate = self.write_session(
            "Acme - WS 2026-07-15 0900",
            meeting=meeting.stem,
            deletion_candidate=True,
        )

        result = ensure_session.ensure_session(self.vault, meeting.stem)

        self.assertEqual(result.action, "created")
        self.assertNotEqual(result.session_path.resolve(), duplicate.resolve())
        self.assertNotIn(
            "duplicate/meeting-source",
            result.session_path.read_text(encoding="utf-8"),
        )
        self.assertEqual(len(list((self.vault / "Work Sessions").glob("*.md"))), 2)

    def test_gong_identity_survives_a_different_meeting_filename(self) -> None:
        self.write_project()
        original = self.write_meeting(
            name="Acme - Original (2026-07-15)", gong_id="gong-123"
        )
        renamed = self.write_meeting(
            name="Acme - Renamed (2026-07-15)", gong_id="gong-123"
        )
        session = self.write_session(
            "Acme - WS 2026-07-15 0900", meeting=original.stem
        )

        result = ensure_session.ensure_session(self.vault, renamed.stem)

        self.assertEqual(result.action, "reused")
        self.assertEqual(result.session_path.resolve(), session.resolve())
        self.assertIn(f'Meeting: "[[{original.stem}]]"', session.read_text(encoding="utf-8"))

    def test_multiple_source_matches_are_a_visible_exception(self) -> None:
        self.write_project()
        meeting = self.write_meeting()
        self.write_session("Acme - WS 2026-07-15 0900", meeting=meeting.stem)
        self.write_session("Acme - WS 2026-07-15 0900 (2)", meeting=meeting.stem)

        with self.assertRaisesRegex(
            ensure_session.EnsureSessionError, "multiple Work Sessions"
        ):
            ensure_session.ensure_session(self.vault, meeting.stem)

    def test_missing_end_time_cannot_seed_a_new_session(self) -> None:
        self.write_project()
        meeting = self.write_meeting(end="")

        with self.assertRaisesRegex(ensure_session.EnsureSessionError, "EndTime"):
            ensure_session.ensure_session(self.vault, meeting.stem)
        self.assertEqual(list((self.vault / "Work Sessions").glob("*.md")), [])

    def test_missing_source_end_reuses_existing_ledger_as_an_exception(self) -> None:
        self.write_project()
        meeting = self.write_meeting(end="")
        session = self.write_session(
            "Acme - WS 2026-07-15 0900", meeting=meeting.stem
        )

        result = ensure_session.ensure_session(self.vault, meeting.stem)

        self.assertEqual(result.action, "reused")
        self.assertEqual(result.session_path.resolve(), session.resolve())
        self.assertIn("Meeting.EndTime is missing", result.warnings[0])

    def test_internal_project_creates_non_billable_internal_session(self) -> None:
        self.write_project(name="Datarails Ongoing", company="")
        meeting = self.write_meeting(
            name="Datarails - Internal (2026-07-15)",
            project="Datarails Ongoing",
            company="",
            bucket="",
        )

        result = ensure_session.ensure_session(self.vault, meeting.stem)
        session_text = result.session_path.read_text(encoding="utf-8")
        meeting_text = meeting.read_text(encoding="utf-8")

        self.assertIn("Company:\n", session_text)
        self.assertIn("ReportingBucket: Internal Operations", session_text)
        self.assertIn("HoursType: Non-billable", session_text)
        self.assertIn("ActivityType: Meeting", session_text)
        self.assertIn("Audience: Internal", session_text)
        self.assertIn("ReportingBucket: Internal Operations", meeting_text)

    def test_unclassifiable_project_is_rejected(self) -> None:
        self.write_project(name="Unclassified Internal", company="")
        meeting = self.write_meeting(
            project="Unclassified Internal", company="", bucket=""
        )

        with self.assertRaisesRegex(
            ensure_session.EnsureSessionError, "no classifiable reporting identity"
        ):
            ensure_session.ensure_session(self.vault, meeting.stem)


if __name__ == "__main__":
    unittest.main()
