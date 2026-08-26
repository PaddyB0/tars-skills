from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "review.py"
SPEC = importlib.util.spec_from_file_location("review", MODULE_PATH)
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review
SPEC.loader.exec_module(review)


class ReviewSessionRollupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def session(self, name, start, minutes, hours="Billable", duplicate=False):
        tags = "tags: [session, duplicate/meeting-source]" if duplicate else "tags: [session]"
        path = self.root / f"{name}.md"
        path.write_text(
            "---\n"
            "fileClass: session\n"
            'Project: "[[Acme - PS Q3 2026]]"\n'
            'Company: "[[Acme]]"\n'
            f"HoursType: {hours}\n"
            f"StartTime: {start}\n"
            f"DurationMin: {minutes}\n"
            f"{tags}\n"
            "---\n",
            encoding="utf-8",
        )
        return path

    def test_cutoff_duplicate_exclusion_and_per_session_rounding(self):
        files = [
            self.session("old", "2026-05-31 23:30", 90),
            self.session("a", "2026-06-01 09:00", 31),
            self.session("b", "2026-06-01 10:00", 31),
            self.session("nonbill", "2026-06-01 11:00", 44, "Non-billable"),
            self.session("duplicate", "2026-06-01 12:00", 100, duplicate=True),
        ]
        result = review.session_rollups(files)
        self.assertEqual(result["included"], 3)
        self.assertEqual(result["raw_min"], 106)
        # 31 -> 60 twice; non-billable retains raw duration but rounds to zero.
        self.assertEqual(result["rounded_billable_min"], 120)
        self.assertEqual(result["by_project"]["Acme - PS Q3 2026"], 106)


if __name__ == "__main__":
    unittest.main()
