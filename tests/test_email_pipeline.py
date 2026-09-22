"""
Unit tests for email pipeline safeguards: study-level eligibility, one-time alerts,
failed sends, the daily-alert switch and the calendar-driven weekly digest.
"""

import sqlite3
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from preuni_system import cli
from preuni_system.calendar import LearningCalendarEngine
from preuni_system.config import Config
from preuni_system.crawler import OpportunityCrawler
from preuni_system.db import Database
from preuni_system.monitor import select_immediate_alert
from preuni_system.utils import is_level_eligible, is_level_relevant


def make_opportunity(opp_id, **overrides):
    opp = {
        "id": opp_id, "title": f"Opportunity {opp_id}", "organizer": "Test Org", "category": "Scholarship",
        "url": f"https://example.org/{opp_id}", "description": "Test description", "deadline": None,
        "eligibility": "Test eligibility", "total_score": 95, "is_immediate_alert": True, "is_active": True,
        "min_level": "pre-university", "max_level": None,
    }
    opp.update(overrides)
    return opp


class TestEmailPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(db_path=Path(self.temp_dir.name) / "test.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def insert(self, *opps):
        with self.db.get_connection() as conn:
            for o in opps:
                conn.execute("""
                INSERT INTO opportunities (id, title, organizer, category, url, description, deadline, eligibility,
                    total_score, is_immediate_alert, is_active, min_level, max_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (o["id"], o["title"], o["organizer"], o["category"], o["url"], o["description"], o["deadline"],
                      o["eligibility"], o["total_score"], int(o["is_immediate_alert"]), int(o["is_active"]),
                      o["min_level"], o["max_level"]))
            conn.commit()

    def run_cli(self, *argv, dispatch_result=None):
        """Run a CLI command against the temporary database with email dispatch mocked out."""
        with patch.object(cli, "Database", return_value=self.db), \
             patch.object(cli.EmailService, "dispatch_email", return_value=dispatch_result) as dispatch, \
             patch.object(sys, "argv", ["preuni", *argv]):
            cli.main()
        return dispatch

    def test_study_level_eligibility(self):
        self.assertTrue(is_level_eligible("pre-university", None, "pre-university"))
        self.assertTrue(is_level_eligible("secondary", None, "pre-university"))
        self.assertFalse(is_level_eligible("200L", None, "pre-university"))
        self.assertFalse(is_level_eligible("secondary", "secondary", "pre-university"))
        self.assertFalse(is_level_eligible("unknown", None, "pre-university"))
        self.assertTrue(is_level_relevant("200L", None, "pre-university"))
        self.assertFalse(is_level_relevant("postgraduate", None, "pre-university"))
        self.assertFalse(is_level_relevant("secondary", "secondary", "pre-university"))

    def test_immediate_alert_picks_only_new_opportunities_open_now(self):
        self.insert(
            make_opportunity("opp-undergrad", total_score=99, min_level="200L"),
            make_opportunity("opp-expired", total_score=98, deadline="2020-01-01"),
            make_opportunity("opp-not-flagged", total_score=97, is_immediate_alert=False),
            make_opportunity("opp-low-score", total_score=80),
            make_opportunity("opp-open", total_score=90),
        )
        chosen = select_immediate_alert(self.db, today=date(2026, 9, 22))
        self.assertEqual(chosen["id"], "opp-open")

        self.db.record_alert_history(chosen["id"], chosen["url"], chosen["title"], "immediate", 4, 90)
        self.assertIsNone(select_immediate_alert(self.db, today=date(2026, 9, 22)))

    def test_alert_is_sent_once_and_recorded(self):
        self.insert(make_opportunity("opp-open"))
        self.run_cli("alert", "--send", dispatch_result={"success": True, "resend_id": "msg-1"})
        self.assertEqual(len(self.db.get_alert_history()), 1)

        dispatch = self.run_cli("alert", "--send", dispatch_result={"success": True, "resend_id": "msg-2"})
        dispatch.assert_not_called()

    def test_failed_send_exits_with_error_and_records_nothing(self):
        self.insert(make_opportunity("opp-open"))
        with self.assertRaises(SystemExit) as ctx:
            self.run_cli("alert", "--send", dispatch_result={"success": False, "error": "HTTP 403: not allowed"})
        self.assertEqual(ctx.exception.code, 1)
        self.assertEqual(self.db.get_alert_history(), [])

    def test_daily_alert_records_history_only_after_a_real_send(self):
        self.db.seed_from_json()
        self.run_cli("daily-alert", "--month", "1", "--week", "2", "--send",
                     dispatch_result={"success": True, "mode": "dry_run / preview"})
        self.assertEqual(self.db.get_alert_history(), [])

        self.run_cli("daily-alert", "--month", "1", "--week", "2", "--send",
                     dispatch_result={"success": True, "resend_id": "msg-1"})
        self.assertGreater(len(self.db.get_alert_history()), 0)

    def test_daily_alert_switch_off_sends_nothing(self):
        with patch.object(Config, "DAILY_ALERT_ENABLED", False):
            dispatch = self.run_cli("daily-alert", "--send", dispatch_result={"success": True, "resend_id": "msg-1"})
        dispatch.assert_not_called()

    def test_digest_follows_calendar_and_splits_open_and_future_opportunities(self):
        self.insert(
            make_opportunity("opp-open", title="Open Now Award"),
            make_opportunity("opp-later", title="Second Year Scholarship", min_level="200L"),
            make_opportunity("opp-phd", title="Doctoral Fellowship", min_level="postgraduate"),
        )
        dispatch = self.run_cli("digest", "--preview", dispatch_result={"success": True, "mode": "dry_run / preview"})
        subject, _, text = dispatch.call_args[0][:3]

        focus = LearningCalendarEngine().get_learning_focus()
        self.assertIn(f"Month {focus.month}, Week {focus.week_in_month}", subject)
        self.assertIn(focus.topic, text)
        open_section, plan_section = text.split("PLAN AHEAD")
        self.assertIn("Open Now Award", open_section)
        self.assertIn("Second Year Scholarship", plan_section)
        self.assertNotIn("Doctoral Fellowship", text)

    def test_crawler_estimates_study_level(self):
        crawler = OpportunityCrawler()
        phd = crawler.clean_and_score_item({"title": "Commonwealth PhD Scholarships 2027", "url": "https://example.org/phd",
                                            "description": "Fully funded doctoral study in the UK"})
        self.assertEqual(phd["min_level"], "postgraduate")
        self.assertFalse(phd["is_immediate_alert"])

        school = crawler.clean_and_score_item({"title": "Essay competition for senior secondary students",
                                               "url": "https://example.org/essay", "description": "Nigeria"})
        self.assertEqual((school["min_level"], school["max_level"]), ("secondary", "secondary"))
        self.assertFalse(school["is_immediate_alert"])

        leavers = crawler.clean_and_score_item({"title": "Health scholarship for school leavers in Nigeria",
                                                "url": "https://example.org/leavers", "description": ""})
        self.assertEqual(leavers["min_level"], "pre-university")
        self.assertTrue(leavers["is_immediate_alert"])

    def test_seeded_undergraduate_scholarships_are_not_immediate_alerts(self):
        self.db.seed_from_json()
        self.assertEqual(self.db.get_opportunity("opp-003")["min_level"], "200L")
        chosen = select_immediate_alert(self.db)
        if chosen:
            self.assertTrue(is_level_eligible(chosen["min_level"], chosen["max_level"]))

    def test_migration_adds_level_columns_to_old_databases(self):
        path = Path(self.temp_dir.name) / "old.sqlite3"
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE opportunities (id TEXT PRIMARY KEY, title TEXT NOT NULL, organizer TEXT NOT NULL, "
                     "category TEXT NOT NULL, url TEXT NOT NULL, is_active INTEGER DEFAULT 1)")
        conn.commit()
        conn.close()

        Database(db_path=path)
        conn = sqlite3.connect(path)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(opportunities)")}
        conn.close()
        self.assertTrue({"min_level", "max_level"} <= columns)


if __name__ == "__main__":
    unittest.main()
