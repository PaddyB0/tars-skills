from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "lint.py"
SPEC = importlib.util.spec_from_file_location("unified_lint_meeting_schema", MODULE_PATH)
assert SPEC and SPEC.loader
lint = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lint
SPEC.loader.exec_module(lint)


class MeetingSchemaContractTests(unittest.TestCase):
    def test_gong_title_is_optional_for_legacy_records_but_requires_gong_identity(self):
        self.assertEqual(lint.phase2_scalar_errors("meeting", {}), [])
        self.assertEqual(
            lint.phase2_scalar_errors("meeting", {"GongId": "123", "GongTitle": "Client sync"}),
            [],
        )
        self.assertIn(
            "Gong metadata requires GongId",
            lint.phase2_scalar_errors("meeting", {"GongTitle": "Client sync"}),
        )

    def test_gong_title_rejects_list_shape(self):
        self.assertIn(
            "GongTitle must be a scalar string",
            lint.phase2_scalar_errors("meeting", {"GongId": "123", "GongTitle": ["Client sync"]}),
        )

    def test_explicit_receipt_and_duration_metadata(self):
        self.assertEqual(
            lint.phase2_scalar_errors("meeting", {
                "GongId": "123",
                "GongTitle": "Client sync",
                "GongReceivedAt": "2026-08-07 16:10",
                "GongDurationMin": 47,
            }),
            [],
        )

    def test_malformed_gong_metadata_fails_closed(self):
        errors = lint.phase2_scalar_errors("meeting", {
            "GongId": 123,
            "GongTitle": {"name": "Client sync"},
            "GongReceivedAt": ["2026-08-07 16:10"],
            "GongDurationMin": "zero",
        })
        self.assertIn("GongId must be a scalar string", errors)
        self.assertIn("GongTitle must be a scalar string", errors)
        self.assertIn("GongReceivedAt must be YYYY-MM-DD HH:mm", errors)
        self.assertIn("GongDurationMin must be a positive integer", errors)
        self.assertIn("Gong metadata requires GongId", errors)

    def test_quoted_number_and_date_only_receipt_are_invalid(self):
        errors = lint.phase2_scalar_errors("meeting", {
            "GongId": "123",
            "GongTitle": "Client sync",
            "GongReceivedAt": "2026-08-07",
            "GongDurationMin": "47",
        })
        self.assertIn("GongReceivedAt must be YYYY-MM-DD HH:mm", errors)
        self.assertIn("GongDurationMin must be a positive integer", errors)

    def test_frontmatter_parser_preserves_gong_number_shape(self):
        unquoted, *_ = lint.parse_frontmatter(
            "---\nfileClass: meeting\nGongId: \"123\"\nGongDurationMin: 47\n---\n"
        )
        quoted, *_ = lint.parse_frontmatter(
            "---\nfileClass: meeting\nGongId: \"123\"\nGongDurationMin: \"47\"\n---\n"
        )
        self.assertEqual(unquoted["GongDurationMin"], 47)
        self.assertEqual(quoted["GongDurationMin"], "47")


if __name__ == "__main__":
    unittest.main()
