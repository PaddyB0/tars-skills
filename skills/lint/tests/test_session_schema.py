from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "lint.py"
SPEC = importlib.util.spec_from_file_location("unified_lint", MODULE_PATH)
assert SPEC and SPEC.loader
lint = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lint
SPEC.loader.exec_module(lint)


class SessionSchemaContractTests(unittest.TestCase):
    def test_final_session_enums(self):
        self.assertEqual(lint.ENUMS["session"]["ActivityType"], {"Meeting", "Build", "Admin"})
        self.assertEqual(lint.ENUMS["session"]["Audience"], {"External", "Internal"})
        self.assertNotIn("SessionType", lint.ENUMS["session"])

    def test_final_links_and_legacy_rejection(self):
        self.assertIn("Task", lint.LINK_FIELDS)
        self.assertIn("Meeting", lint.LINK_FIELDS)
        self.assertNotIn("TaskName", lint.LINK_FIELDS)
        self.assertEqual(
            lint.LEGACY_SESSION_FIELDS,
            {"TaskName", "ProjectName", "StartDate", "EndDate", "SessionType", "Completed"},
        )


if __name__ == "__main__":
    unittest.main()
