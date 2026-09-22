"""
Unit tests for dashboard support: saved-progress handling (dashboard/progress.js), shared
progress applied by the seed step, and the email previews rendered for the Emails tab.
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from preuni_system.bundle_dashboard import render_email_previews
from preuni_system.db import Database
from preuni_system.utils import normalize_url

REPO_DIR = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")

PROGRESS_JS_CHECKS = r"""
const assert = require("assert");
const P = require(process.argv[1]);

// Version 1 saved whole course objects (with old links) and a demo project
const v1 = {
  courses: [{ id: "crs-1", status: "Completed", url: "https://old.example/broken" }, { id: "crs-2", status: "Not started" }],
  tailoring_projects: [{ id: "tailor-001", project_name: "Demo" }, { id: "tailor-123", project_name: "Mine" }],
  checklist_completed: [3],
  rubric_scores: { "1": { communication: 4 } }
};
const state = P.normalizeState(v1, "2026-09-22T00:00:00Z");
assert.deepStrictEqual(state.course_progress, { "crs-1": { status: "Completed", updated: "2026-09-22T00:00:00Z" } });
assert.deepStrictEqual(state.tailoring_projects.map(p => p.id), ["tailor-123"]);

// Course details come from the latest data; only the status comes from saved progress
const courses = P.applyProgress([{ id: "crs-1", url: "https://new.example/fixed", status: "Not started" }], state.course_progress, "Not started");
assert.strictEqual(courses[0].url, "https://new.example/fixed");
assert.strictEqual(courses[0].status, "Completed");

// The most recently updated status wins
const merged = P.mergeProgress({ a: { status: "Completed", updated: "2026-01-02" } }, { a: { status: "In progress", updated: "2026-01-01" } });
assert.strictEqual(merged.a.status, "Completed");

// Restoring a backup keeps entries from both sides
const restored = P.mergeStates(state, { version: 2, tailoring_projects: [{ id: "tailor-999" }], checklist_completed: [5] });
assert.deepStrictEqual(restored.tailoring_projects.map(p => p.id).sort(), ["tailor-123", "tailor-999"]);
assert.deepStrictEqual(restored.checklist_completed.sort(), [3, 5]);

// The shared progress file holds statuses only
const shared = P.buildSharedProgress(restored, "2026-09-22");
assert.deepStrictEqual(Object.keys(shared).sort(), ["courses", "reading", "updated"]);

// Eligibility matches preuni_system.utils
assert.ok(P.isLevelEligible("pre-university", null, "pre-university"));
assert.ok(!P.isLevelEligible("200L", null, "pre-university"));
assert.ok(P.isLevelRelevant("200L", null, "pre-university"));
assert.ok(!P.isLevelRelevant("secondary", "secondary", "pre-university"));
assert.ok(!P.isLevelRelevant("postgraduate", null, "pre-university"));
console.log("ok");
"""


class TestDashboard(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @unittest.skipUnless(NODE, "node is not installed")
    def test_saved_progress_helpers(self):
        result = subprocess.run([NODE, "-e", PROGRESS_JS_CHECKS, str(REPO_DIR / "dashboard" / "progress.js")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_seed_applies_shared_progress_file(self):
        data_dir = self.tmp / "data"
        data_dir.mkdir()
        for name in ("courses.json", "reading_list.json"):
            shutil.copy(REPO_DIR / "data" / name, data_dir)
        (data_dir / "progress.json").write_text(json.dumps({
            "courses": {"crs-bio-001": {"status": "Completed", "updated": "2026-09-22"},
                        "crs-bio-002": {"status": "Not a real status"}},
            "reading": {"read-001": {"status": "Completed", "updated": "2026-09-22"}}
        }), encoding="utf-8")

        db = Database(db_path=self.tmp / "test.sqlite3")
        with patch("preuni_system.db.DATA_DIR", data_dir):
            stats = db.seed_from_json()

        self.assertEqual(stats["progress"], 2)
        course_url = next(c["url"] for c in json.load(open(data_dir / "courses.json")) if c["id"] == "crs-bio-001")
        self.assertIn(normalize_url(course_url), db.get_completed_course_urls())

    def test_bundle_renders_email_previews(self):
        out_dir = self.tmp / "emails"
        render_email_previews(out_dir)
        for name in ("daily_alert", "weekly_digest", "immediate_alert"):
            self.assertTrue((out_dir / f"{name}.html").read_text(encoding="utf-8").strip())
        self.assertIn("DAILY LEARNING GUIDE", (out_dir / "daily_alert.html").read_text(encoding="utf-8"))
        self.assertIn("Weekly Development Digest", (out_dir / "weekly_digest.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
