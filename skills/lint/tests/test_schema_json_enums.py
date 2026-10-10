from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "lint.py"


def load_lint(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Copied verbatim from the literal ENUMS dict lint.py carried before it was
# derived from schema.json; pins that the derivation changes no behaviour.
EXPECTED_ENUMS = {
    "task": {
        "Status": {"⚫ BACKLOG", "⚪ TO DO", "🔵 IN PROGRESS",
                   "🟣 HUMAN REVIEW", "🟠 REWORK", "🟢 MERGING",
                   "🟢 COMPLETE", "⚫ CANCELED", "⚫ DUPLICATE"},
        "Priority": {"Low", "Medium", "High", "Critical"},
        "Phase": {"Kick-Off", "Change Planning", "Workspace Configuration",
                  "Model Builds", "Dashboard Design", "Training + Enablement"},
        "Visibility": {"client facing", "internal"},
        "Executor": {"Patrick", "Code-Mac", "Code-Win", "Code-Work", "Cowork"},
        "Workflow": {"dr-recon", "dr-lut-diagnose"},
        "Repeat": {"daily", "weekly", "monthly", "yearly"},
        "ScheduleMode": {"flexible", "fixed", "manual"},
        "Energy": {"deep", "shallow", "any"},
    },
    "habit": {
        "Status": {"active", "paused", "retired"},
        "Priority": {"Low", "Medium", "High", "Critical"},
        "Cadence": {"daily", "weekly"},
        "DaysOfWeek": {
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        },
        "CatchUpPolicy": {"skip", "rollover-once", "catch-up-capped"},
        "CalendarVisibility": {"default", "private"},
    },
    "scheduling_policy": {
        "DefaultVisibility": {"default", "private"},
        "ApplyMode": {"assisted", "automatic"},
    },
    "project": {
        "Status": {"🟠 backlog", "⚪ planned", "🔵 active", "🔴 at risk", "🟢 complete"},
        "Type": {"Premium Success", "CS Hours", "AI Transformation Services"},
        "ScopeCategory": {"40+ hrs", "26-39 hrs", "11-25 hrs", "0-10 hrs"},
        "HubIcon": {"rocket", "folder-kanban", "briefcase-business",
                    "chart-no-axes-column", "building-2", "target", "sparkles", "wrench"},
        "HubColor": {"blue", "green", "purple", "cyan",
                     "orange", "pink", "yellow", "red"},
    },
    "session": {
        "HoursType": {"Billable", "Non-billable"},
        "ActivityType": {"Meeting", "Build", "Admin"},
        "Audience": {"External", "Internal"},
        "ReportingBucket": {"Client Delivery", "Internal Operations", "TARS / OS"},
    },
    "meeting": {
        "CallType": {"internal call", "external call"},
        "ReportingBucket": {"Client Delivery", "Internal Operations", "TARS / OS"},
        "CalendarProvider": {"reclaim", "google", "outlook"},
    },
    "crm_company": {
        "Type": {"Company", "Contact"},
        "Timezone": {"EST", "PST", "MST", "CDT"},
    },
    "crm_contacts": {
        "contact.recordtype": {"Decision Maker", "Champion", "Contact"},
        "Type": {"Company", "Contact"},
        "Timezone": {"EST", "PST", "MST", "CDT"},
    },
}


class SchemaJsonEnumsTests(unittest.TestCase):
    def test_enums_derived_from_schema_json_match_the_former_literal(self):
        lint = load_lint(MODULE_PATH, "unified_lint_schema_json_enums")
        self.assertEqual(lint.ENUMS, EXPECTED_ENUMS)

    def test_missing_schema_json_fails_at_import(self):
        with tempfile.TemporaryDirectory() as td:
            copy = Path(td) / "lint.py"
            shutil.copyfile(MODULE_PATH, copy)
            with self.assertRaises(FileNotFoundError):
                load_lint(copy, "unified_lint_schema_json_missing")

    def test_invalid_schema_json_fails_at_import(self):
        with tempfile.TemporaryDirectory() as td:
            copy = Path(td) / "lint.py"
            shutil.copyfile(MODULE_PATH, copy)
            (Path(td) / "schema.json").write_text("{not json", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_lint(copy, "unified_lint_schema_json_invalid")


if __name__ == "__main__":
    unittest.main()
