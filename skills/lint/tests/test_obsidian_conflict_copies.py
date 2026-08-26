from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


LINTER = Path(__file__).parents[1] / "lint.py"
SPEC = importlib.util.spec_from_file_location("unified_lint_conflict_copies", LINTER)
assert SPEC and SPEC.loader
lint = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lint
SPEC.loader.exec_module(lint)


def run_lint(vault: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(LINTER),
            "--vault",
            str(vault),
            "--today",
            "2026-08-11",
            *extra_args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


class ObsidianConflictCopyFilenameTests(unittest.TestCase):
    def test_recognizes_anchored_official_filenames(self):
        self.assertTrue(
            lint.is_obsidian_conflict_copy_filename(
                "Project plan (Conflicted copy Patricks MacBook Pro 202608111908).md"
            )
        )
        self.assertTrue(
            lint.is_obsidian_conflict_copy_filename(
                "settings (Conflicted copy Windows-Laptop 202608111908).json"
            )
        )

    def test_rejects_ordinary_names_paths_and_bad_timestamps(self):
        non_conflicts = (
            "plugin-conflict.js",
            "parent (Conflicted copy Device 202608111908)/ordinary.md",
            "Note (Conflicted copy Device).md",
            "Note (Conflicted copy Device 2026-08-11 1908).md",
            "Note (Conflicted copy Device 20260811190).md",
            "Note (conflicted copy Device 202608111908).md",
            "Note (Conflicted copy Device 202608111908)",
        )
        for name in non_conflicts:
            with self.subTest(name=name):
                self.assertFalse(lint.is_obsidian_conflict_copy_filename(name))


class ObsidianConflictCopyScanTests(unittest.TestCase):
    def test_non_markdown_conflict_copy_anywhere_in_vault_is_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            conflict = (
                vault
                / "System"
                / "runtime"
                / "settings (Conflicted copy Windows Laptop 202608111908).json"
            )
            conflict.parent.mkdir(parents=True)
            conflict.write_text('{"setting": true}\n', encoding="utf-8")

            result = run_lint(vault)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(
            "System/runtime/settings (Conflicted copy Windows Laptop "
            "202608111908).json",
            result.stdout,
        )
        self.assertIn("Obsidian conflict-copy filename", result.stdout)

    def test_git_and_symlink_entries_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            internal = (
                vault
                / ".git"
                / "Note (Conflicted copy Device 202608111908).md"
            )
            internal.parent.mkdir()
            internal.write_text("git internal\n", encoding="utf-8")
            outside = vault.parent / f"{vault.name}-outside"
            outside.write_text("outside\n", encoding="utf-8")
            link = vault / "Link (Conflicted copy Device 202608111908).md"
            try:
                link.symlink_to(outside)
                result = run_lint(vault)
            finally:
                outside.unlink(missing_ok=True)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Obsidian conflict-copy filename", result.stdout)

    def test_fix_never_changes_or_removes_a_conflict_copy(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            conflict = vault / "Note (Conflicted copy Device 202608111908).md"
            original = b"preserve exact conflict evidence\n"
            conflict.write_bytes(original)

            result = run_lint(vault, "--fix")

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertTrue(conflict.exists())
            self.assertEqual(conflict.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
