from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "lint.py"
SPEC = importlib.util.spec_from_file_location("unified_lint_agent_surface", MODULE_PATH)
assert SPEC and SPEC.loader
lint = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lint
SPEC.loader.exec_module(lint)


FAKE_FINDINGS_SCRIPT = """\
import json, sys
print(json.dumps({
    "findings": [
        {"code": "AS1", "path": ".claude/settings.json", "line": 3,
         "message": "invalid JSON at line 3 column 1: Expecting value"},
        {"code": "AS5", "path": "CLAUDE.md", "line": None,
         "message": "always-loaded word total 8200 exceeds ceiling 7000"},
    ],
    "words": {"total": 8200, "ceiling": 7000},
    "status": "fail",
}))
sys.exit(1)
"""

FAKE_CLEAN_SCRIPT = """\
import json, sys
print(json.dumps({
    "findings": [],
    "words": {"total": 6485, "ceiling": 7000},
    "status": "pass",
}))
sys.exit(0)
"""

FAKE_EXIT2_SCRIPT = """\
import sys
print("agent_surface_lint: internal error: boom", file=sys.stderr)
sys.exit(2)
"""

FAKE_BAD_JSON_SCRIPT = """\
import sys
print("not json")
sys.exit(0)
"""

FAKE_JSON_LIST_SCRIPT = """\
import json, sys
print(json.dumps([]))
sys.exit(0)
"""

FAKE_NULL_FINDINGS_SCRIPT = """\
import json, sys
print(json.dumps({"findings": None}))
sys.exit(0)
"""


def _write_fake_agent_surface_lint(vault_root: Path, body: str) -> None:
    scripts_dir = vault_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script = scripts_dir / "agent_surface_lint.py"
    script.write_text(body, encoding="utf-8")


class AgentSurfacePassTests(unittest.TestCase):
    def test_findings_become_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp)
            _write_fake_agent_surface_lint(vault_root, FAKE_FINDINGS_SCRIPT)
            errors, warnings, summary = lint.run_agent_surface_pass(str(vault_root))
            self.assertEqual(len(errors), 2)
            self.assertEqual(errors[0], (".claude/settings.json:3",
                                          "AS1: invalid JSON at line 3 column 1: "
                                          "Expecting value"))
            self.assertEqual(errors[1], ("CLAUDE.md",
                                          "AS5: always-loaded word total 8200 "
                                          "exceeds ceiling 7000"))
            self.assertEqual(warnings, [])
            self.assertIn("8200", summary)
            self.assertIn("7000", summary)
            self.assertIn("fail", summary)

    def test_clean_run_reports_word_total_with_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp)
            _write_fake_agent_surface_lint(vault_root, FAKE_CLEAN_SCRIPT)
            errors, warnings, summary = lint.run_agent_surface_pass(str(vault_root))
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            self.assertIn("6485", summary)
            self.assertIn("pass", summary)

    def test_missing_script_becomes_one_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp)
            errors, warnings, summary = lint.run_agent_surface_pass(str(vault_root))
            self.assertEqual(errors, [])
            self.assertEqual(len(warnings), 1)
            self.assertIn("agent-surface lint not installed", warnings[0][1])

    def test_exit_2_becomes_one_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp)
            _write_fake_agent_surface_lint(vault_root, FAKE_EXIT2_SCRIPT)
            errors, warnings, summary = lint.run_agent_surface_pass(str(vault_root))
            self.assertEqual(len(errors), 1)
            self.assertIn("exited 2", errors[0][1])
            self.assertIn("boom", errors[0][1])
            self.assertEqual(warnings, [])

    def test_invalid_json_becomes_one_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp)
            _write_fake_agent_surface_lint(vault_root, FAKE_BAD_JSON_SCRIPT)
            errors, warnings, summary = lint.run_agent_surface_pass(str(vault_root))
            self.assertEqual(len(errors), 1)
            self.assertIn("invalid JSON", errors[0][1])
            self.assertEqual(warnings, [])

    def test_json_that_is_a_list_becomes_one_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp)
            _write_fake_agent_surface_lint(vault_root, FAKE_JSON_LIST_SCRIPT)
            errors, warnings, summary = lint.run_agent_surface_pass(str(vault_root))
            self.assertEqual(len(errors), 1)
            self.assertIn("unexpected JSON shape", errors[0][1])
            self.assertEqual(warnings, [])

    def test_null_findings_field_becomes_one_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp)
            _write_fake_agent_surface_lint(vault_root, FAKE_NULL_FINDINGS_SCRIPT)
            errors, warnings, summary = lint.run_agent_surface_pass(str(vault_root))
            self.assertEqual(len(errors), 1)
            self.assertIn("unexpected JSON shape", errors[0][1])
            self.assertEqual(warnings, [])

    def test_unlaunchable_interpreter_becomes_one_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp)
            _write_fake_agent_surface_lint(vault_root, FAKE_CLEAN_SCRIPT)
            original_executable = lint.sys.executable
            lint.sys.executable = str(Path(tmp) / "does-not-exist-python-binary")
            try:
                errors, warnings, summary = lint.run_agent_surface_pass(str(vault_root))
            finally:
                lint.sys.executable = original_executable
            self.assertEqual(len(errors), 1)
            self.assertIn("could not start", errors[0][1])
            self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
