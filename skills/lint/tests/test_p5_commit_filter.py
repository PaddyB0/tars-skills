from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "lint.py"
SPEC = importlib.util.spec_from_file_location("unified_lint_p5", MODULE_PATH)
assert SPEC and SPEC.loader
lint = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lint
SPEC.loader.exec_module(lint)


class P5CommitFilterTests(unittest.TestCase):
    def test_client_delivery_subjects_still_count(self):
        self.assertTrue(
            lint.p5_subject_is_delivery(
                "Acme: apply + verify revenue double-count fix"
            )
        )
        self.assertTrue(lint.p5_subject_is_delivery("vault backup: 2026-07-24 03:24:32"))

    def test_os_cleanup_and_ingestion_subjects_do_not_count(self):
        self.assertFalse(
            lint.p5_subject_is_delivery("Clean up TARS dead capability routes")
        )
        self.assertFalse(
            lint.p5_subject_is_delivery("Clean up TARS routing and portfolio index")
        )
        self.assertFalse(lint.p5_subject_is_delivery("Ingest Q3 meeting backlog"))


if __name__ == "__main__":
    unittest.main()
