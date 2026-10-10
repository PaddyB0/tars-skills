from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SKILLS_ROOT = Path(__file__).parents[2]
LINTERS = (
    SKILLS_ROOT / "lint" / "lint.py",
)


def load_linter(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_note(vault: Path, relative_path: str, frontmatter: str) -> None:
    path = vault / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n" + textwrap.dedent(frontmatter).strip() + "\n---\n",
        encoding="utf-8",
    )


def run_linter(linter: Path, vault: Path) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(linter), "--vault", str(vault)]
    if linter.parent.name == "lint":
        command.extend(("--today", "2026-07-28"))
    return subprocess.run(command, capture_output=True, text=True, check=False)


class EnumCoverageTests(unittest.TestCase):
    def test_cover_repeat_and_calendar_provider(self):
        for index, path in enumerate(LINTERS):
            with self.subTest(linter=path.parent.name):
                lint = load_linter(path, f"milestone_contract_lint_{index}")
                self.assertEqual(
                    lint.ENUMS["task"]["Repeat"],
                    {"daily", "weekly", "monthly", "yearly"},
                )
                self.assertEqual(
                    lint.ENUMS["meeting"]["CalendarProvider"],
                    {"reclaim", "google", "outlook"},
                )


class MilestoneRelationshipTests(unittest.TestCase):
    def test_valid_project_milestone_task_relationship_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            write_note(
                vault,
                "Projects/Alpha.md",
                """
                fileClass: project
                Status: 🔵 active
                tags: [project]
                """,
            )
            write_note(
                vault,
                "Milestones/Alpha - MS - Launch.md",
                """
                fileClass: milestone
                Project: "[[Alpha]]"
                tags: [milestone]
                """,
            )
            write_note(
                vault,
                "Tasks/Launch work.md",
                """
                fileClass: task
                Project: "[[Alpha]]"
                Milestone: "[[Alpha - MS - Launch]]"
                tags: [task]
                """,
            )

            for linter in LINTERS:
                with self.subTest(linter=linter.parent.name):
                    result = run_linter(linter, vault)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertNotIn("ERRORS", result.stdout)

    def test_invalid_tags_typed_links_ownership_and_prefix_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            for project in ("Alpha", "Beta"):
                write_note(
                    vault,
                    f"Projects/{project}.md",
                    f"""
                    fileClass: project
                    Status: 🔵 active
                    tags: [project]
                    """,
                )
            write_note(
                vault,
                "Milestones/Alpha - MS - Launch.md",
                """
                fileClass: milestone
                Project: "[[Alpha]]"
                tags: [milestone]
                """,
            )
            write_note(
                vault,
                "Milestones/Wrong - MS - Prefix.md",
                """
                fileClass: milestone
                Project: "[[Alpha]]"
                tags: [milestone]
                """,
            )
            write_note(
                vault,
                "Milestones/Multi - MS - Project.md",
                """
                fileClass: milestone
                Project: ["[[Alpha]]", "[[Beta]]"]
                tags: [milestone]
                """,
            )
            write_note(
                vault,
                "Tasks/Cross project.md",
                """
                fileClass: task
                Project: "[[Beta]]"
                Milestone: "[[Alpha - MS - Launch]]"
                tags: [task]
                """,
            )
            write_note(
                vault,
                "Tasks/Wrong target.md",
                """
                fileClass: task
                Project: "[[Alpha]]"
                Milestone: "[[Alpha]]"
                tags: [task]
                """,
            )
            write_note(
                vault,
                "Tasks/Wrong tag.md",
                """
                fileClass: task
                Project: "[[Alpha]]"
                tags: [project]
                """,
            )

            expected = (
                "tags must include canonical 'task'",
                "milestone Project must contain exactly one project wikilink",
                "Task.Milestone must target a milestone note",
                "task Project [[Beta]] does not match milestone Project [[Alpha]]",
                "milestone filename must start with linked project 'Alpha - MS - '",
            )
            for linter in LINTERS:
                with self.subTest(linter=linter.parent.name):
                    result = run_linter(linter, vault)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    for message in expected:
                        self.assertIn(message, result.stdout)


if __name__ == "__main__":
    unittest.main()
