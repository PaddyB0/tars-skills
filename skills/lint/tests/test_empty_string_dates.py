import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


LINTER = Path(__file__).parents[1] / "lint.py"


class EmptyStringDateTests(unittest.TestCase):
    def test_quoted_empty_task_date_is_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            task = vault / "Tasks" / "Acme - Empty Date.md"
            task.parent.mkdir(parents=True)
            task.write_text(
                "---\n"
                "fileClass: task\n"
                "tags: [task]\n"
                "Status: ⚪ TO DO\n"
                "Priority: High\n"
                'DueDate: ""\n'
                "---\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(LINTER), "--vault", str(vault)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("empty-string date DueDate", result.stdout)


if __name__ == "__main__":
    unittest.main()
