from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


LINTER = Path(__file__).parents[1] / "lint.py"


def _find_repo_root(start: Path) -> Path:
    """Walk upward from `start` until a directory holding both CLAUDE.md and
    Administrator/ is found. A fixed parents[N] depth breaks depending on
    whether this test runs from the canonical source tree
    (System/Agent Runtime/source/claude/skills/lint/tests) or its `.claude/`
    projection (.claude/skills/lint/tests) — the two sit at different depths
    below the repo root."""
    for candidate in (start, *start.parents):
        if (candidate / "CLAUDE.md").is_file() and (candidate / "Administrator").is_dir():
            return candidate
    # Outside a TARS checkout, skip instead of failing collection for the
    # rest of the suite: these tests read the live FileClass and templates.
    raise unittest.SkipTest(f"TARS checkout not found above {start}")


ROOT = _find_repo_root(Path(__file__).resolve().parent)


def load_linter():
    spec = importlib.util.spec_from_file_location("scheduler_phase2_lint", LINTER)
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


def run_lint(vault: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(LINTER),
            "--vault",
            str(vault),
            "--today",
            "2026-07-30",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def valid_policy() -> str:
    return """
        fileClass: scheduling_policy
        UID: 0f80f5cc-4474-4acd-b220-f1f902dea771
        Timezone: America/Edmonton
        MondayWindow: 08:30-17:00
        TuesdayWindow: 08:30-17:00
        WednesdayWindow: 08:30-17:00
        ThursdayWindow: 08:30-17:00
        FridayWindow: 08:30-16:00
        MeetingWindow: 09:00-16:00
        NoMeetingWindows: Protect lunch and existing focus blocks
        DeepWorkWindow: 08:30-11:30
        ShallowWorkWindow: 13:00-16:00
        NormalHoursWindow: 09:00-17:00
        DefaultTaskMinBlockMin: 30
        DefaultTaskMaxBlockMin: 120
        DefaultHabitDurationMin: 30
        DailyCapacityMin: 420
        WeeklyCapacityMin: 2100
        MeetingPrepMin: 10
        TravelBufferMin: 0
        DecompressionMin: 10
        WorkBreakMin: 5
        SoftFreezeHours: 24
        HardLockHours: 2
        TargetCalendar: TARS Schedule
        DefaultVisibility: private
        ApplyMode: assisted
        Description: Default workweek
        tags: [scheduling_policy]
    """


class SchedulerPhase2ConstantTests(unittest.TestCase):
    def test_locked_fileclasses_folders_tags_and_enums_are_registered(self):
        lint = load_linter()

        self.assertEqual(lint.FOLDERS["habit"], "Habits")
        self.assertEqual(
            lint.FOLDERS["scheduling_policy"],
            "Scheduling Policies",
        )
        self.assertEqual(lint.FILECLASS_TAG["habit"], "habit")
        self.assertEqual(
            lint.FILECLASS_TAG["scheduling_policy"],
            "scheduling_policy",
        )
        self.assertEqual(
            lint.ENUMS["task"]["ScheduleMode"],
            {"flexible", "fixed", "manual"},
        )
        self.assertEqual(
            lint.ENUMS["task"]["Energy"],
            {"deep", "shallow", "any"},
        )
        self.assertEqual(
            lint.ENUMS["habit"]["DaysOfWeek"],
            {
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            },
        )
        self.assertEqual(
            lint.ENUMS["scheduling_policy"]["ApplyMode"],
            {"assisted", "automatic"},
        )

    def test_fileclasses_and_templates_carry_the_locked_fields_and_safe_defaults(self):
        task_class = (
            ROOT / "Administrator" / "FileClasses" / "task.md"
        ).read_text(encoding="utf-8")
        habit_class = (
            ROOT / "Administrator" / "FileClasses" / "habit.md"
        ).read_text(encoding="utf-8")
        policy_class = (
            ROOT / "Administrator" / "FileClasses" / "scheduling_policy.md"
        ).read_text(encoding="utf-8")
        for field in (
            "UID",
            "AutoSchedule",
            "ScheduleMode",
            "MinBlockMin",
            "MaxBlockMin",
            "SchedulingPolicy",
            "Energy",
        ):
            self.assertIn(f"- name: {field}", task_class)
        for field in (
            "UID",
            "Status",
            "Cadence",
            "TargetCount",
            "DaysOfWeek",
            "DurationMin",
            "EarliestTime",
            "PreferredTime",
            "LatestTime",
            "SchedulingPolicy",
            "CatchUpPolicy",
            "CalendarVisibility",
            "StartDate",
            "EndDate",
        ):
            self.assertIn(f"- name: {field}", habit_class)
        for field in (
            "MondayWindow",
            "SundayWindow",
            "NoMeetingWindows",
            "DeepWorkWindow",
            "ShallowWorkWindow",
            "NormalHoursWindow",
            "DefaultTaskMinBlockMin",
            "DefaultTaskMaxBlockMin",
            "DailyCapacityMin",
            "WeeklyCapacityMin",
            "SoftFreezeHours",
            "HardLockHours",
            "TargetCalendar",
            "ApplyMode",
        ):
            self.assertIn(f"- name: {field}", policy_class)
        self.assertIn(
            "type: Input",
            policy_class.split("- name: NoMeetingWindows", 1)[1].split(
                "- name:", 1
            )[0],
        )

        for template_name in (
            "Task Template.md",
            "Habit Template.md",
            "Scheduling Policy Template.md",
        ):
            template = (
                ROOT / "Administrator" / "Templates" / template_name
            ).read_text(encoding="utf-8")
            self.assertIn("crypto.randomUUID()", template)
            self.assertIn("UID: <% _uid %>", template)
        task_template = (
            ROOT / "Administrator" / "Templates" / "Task Template.md"
        ).read_text(encoding="utf-8")
        self.assertIn("ScheduleMode: manual", task_template)


class SchedulerPhase2LintTests(unittest.TestCase):
    def test_legacy_task_without_uid_remains_valid(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            write_note(
                vault,
                "Tasks/Acme - Legacy.md",
                """
                fileClass: task
                Status: ⚪ TO DO
                Priority: Medium
                tags: [task]
                """,
            )

            result = run_lint(vault)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("requires UID", result.stdout)

    def test_scheduler_uids_are_globally_unique_across_record_types(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            shared_uid = "5165a614-0f22-4a44-8478-2348631459e7"
            write_note(
                vault,
                "Tasks/Acme - Duplicate UID.md",
                f"""
                fileClass: task
                UID: {shared_uid}
                Status: ⚪ TO DO
                tags: [task]
                """,
            )
            write_note(
                vault,
                "Habits/TARS - Habit - Duplicate UID.md",
                f"""
                fileClass: habit
                UID: {shared_uid}
                Status: paused
                tags: [habit]
                """,
            )

            result = run_lint(vault)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("duplicate scheduler UID"), 2)

    def test_valid_task_habit_and_policy_contract_passes(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            write_note(
                vault,
                "Scheduling Policies/Scheduling Policy - Default Workweek.md",
                valid_policy(),
            )
            write_note(
                vault,
                "Tasks/Acme - Scheduled work.md",
                """
                fileClass: task
                UID: 5165a614-0f22-4a44-8478-2348631459e7
                Status: ⚪ TO DO
                Priority: High
                Estimate: 2
                DueDate: 2026-08-01
                AutoSchedule: true
                ScheduleMode: flexible
                MinBlockMin: 30
                MaxBlockMin: 90
                SchedulingPolicy: "[[Scheduling Policy - Default Workweek]]"
                Energy: deep
                tags: [task]
                """,
            )
            write_note(
                vault,
                "Habits/TARS - Habit - Weekly Review.md",
                """
                fileClass: habit
                UID: 8c30d9ca-97e8-4a69-87ef-4f205c95f6e0
                Status: active
                Priority: Medium
                Cadence: weekly
                TargetCount: 1
                DaysOfWeek:
                  - friday
                DurationMin: 45
                EarliestTime: 09:00
                LatestTime: 16:00
                SchedulingPolicy: "[[Scheduling Policy - Default Workweek]]"
                CatchUpPolicy: skip
                CalendarVisibility: private
                StartDate: 2026-07-30
                Description: Review the operating system
                tags: [habit]
                """,
            )

            result = run_lint(vault)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("ERRORS", result.stdout)

    def test_invalid_auto_schedule_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            write_note(
                vault,
                "Tasks/Acme - Invalid candidate.md",
                """
                fileClass: task
                Status: ⚪ TO DO
                AutoSchedule: true
                SyncToReclaim: true
                ScheduleMode: fixed
                MinBlockMin: 60
                MaxBlockMin: 30
                SchedulingPolicy: "[[Missing Policy]]"
                tags: [task]
                """,
            )

            result = run_lint(vault)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for expected in (
            "AutoSchedule cannot be true when SyncToReclaim is true",
            "AutoSchedule requires UID",
            "AutoSchedule requires ScheduleMode: flexible",
            "AutoSchedule requires exactly one SchedulingPolicy link to a scheduling_policy note",
            "MinBlockMin must be less than or equal to MaxBlockMin",
        ):
            self.assertIn(expected, result.stdout)

    def test_active_habit_contract_is_strict_but_paused_habit_can_be_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            write_note(
                vault,
                "Habits/TARS - Habit - Invalid.md",
                """
                fileClass: habit
                Status: active
                Priority: High
                Cadence: weekly
                TargetCount: 0
                DurationMin: 22.5
                EarliestTime: 16:00
                PreferredTime: 08:00
                LatestTime: 09:00
                SchedulingPolicy: "[[Missing Policy]]"
                CatchUpPolicy: skip
                CalendarVisibility: default
                StartDate: 2026-07-30 09:00
                tags: [habit]
                """,
            )
            write_note(
                vault,
                "Habits/TARS - Habit - Paused.md",
                """
                fileClass: habit
                Status: paused
                Priority: Low
                Cadence: daily
                CatchUpPolicy: skip
                CalendarVisibility: private
                tags: [habit]
                """,
            )
            write_note(
                vault,
                "Habits/TARS - Habit - Missing window.md",
                """
                fileClass: habit
                UID: b475f6ce-72a8-4e9b-8ce1-dbc6e14dc591
                Status: active
                Cadence: daily
                TargetCount: 1
                DurationMin: 30
                SchedulingPolicy: "[[Missing Policy]]"
                tags: [habit]
                """,
            )

            result = run_lint(vault)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for expected in (
            "active habit requires UID",
            "active habit TargetCount must be a positive integer",
            "active habit DurationMin must be a positive integer",
            "weekly active habit requires DaysOfWeek",
            "active habit requires exactly one SchedulingPolicy link to a scheduling_policy note",
            "habit time order must be EarliestTime <= PreferredTime <= LatestTime",
            "habit StartDate must be date-only",
            "active habit requires EarliestTime and LatestTime in HH:mm",
        ):
            self.assertIn(expected, result.stdout)
        self.assertNotIn("TARS - Habit - Paused.md\n     ✗", result.stdout)

    def test_policy_requires_safe_flat_values_and_time_ranges(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            write_note(
                vault,
                "Scheduling Policies/Scheduling Policy - Invalid.md",
                """
                fileClass: scheduling_policy
                MondayWindow: 17:00-09:00
                MeetingWindow: 25:00-26:00
                NoMeetingWindows: Protect lunch
                DeepWorkWindow:
                ShallowWorkWindow: [09:00-10:00]
                NormalHoursWindow: 17:00-09:00
                DefaultTaskMinBlockMin: 120
                DefaultTaskMaxBlockMin: 60
                DefaultHabitDurationMin: 0
                DailyCapacityMin: -1
                WeeklyCapacityMin: 0
                MeetingPrepMin: -1
                TravelBufferMin: 0
                DecompressionMin: 0
                WorkBreakMin: 0
                SoftFreezeHours: 1
                HardLockHours: 2
                tags: [scheduling_policy]
                """,
            )

            result = run_lint(vault)

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for expected in (
            "scheduling policy requires UID",
            "scheduling policy requires Timezone",
            "invalid MondayWindow",
            "invalid MeetingWindow",
            "invalid DeepWorkWindow",
            "invalid ShallowWorkWindow",
            "invalid NormalHoursWindow",
            "DefaultHabitDurationMin must be a positive integer",
            "DailyCapacityMin must be a positive integer",
            "WeeklyCapacityMin must be a positive integer",
            "MeetingPrepMin must be a nonnegative integer",
            "DefaultTaskMinBlockMin must be less than or equal to DefaultTaskMaxBlockMin",
            "HardLockHours must be less than or equal to SoftFreezeHours",
            "scheduling policy requires TargetCalendar",
            "scheduling policy requires DefaultVisibility",
            "scheduling policy requires ApplyMode",
        ):
            self.assertIn(expected, result.stdout)


if __name__ == "__main__":
    unittest.main()
