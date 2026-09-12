"""
Unit tests for Daily Alert Generation, Templates, and CLI dispatch.
"""

import unittest
from unittest.mock import patch
import sys
from preuni_system.calendar import LearningCalendarEngine
from preuni_system.emailer import EmailService
from preuni_system.models import OpportunityAlertMatch, DailyLearningFocus
from preuni_system.cli import main


class TestDailyAlert(unittest.TestCase):

    def setUp(self):
        self.calendar = LearningCalendarEngine(start_date_str="2026-09-01")
        self.emailer = EmailService()

    def test_build_daily_alert_template_with_recommendations(self):
        focus = self.calendar.get_learning_focus(month=1, week=2)
        learn_now = [
            OpportunityAlertMatch(
                opportunity_id="crs-test-chm-01",
                title="High School Chemistry: Atomic Structure",
                provider="Khan Academy",
                url="https://khanacademy.org/chemistry",
                category="Chemistry",
                match_type="learn_now",
                relevance_score=92,
                why_it_matches="Directly covers electron configurations for this week.",
                estimated_time="45 mins",
                cost="Free"
            )
        ]
        long_term = [
            OpportunityAlertMatch(
                opportunity_id="crs-test-res-01",
                title="Research Methods in Health",
                provider="Coursera",
                url="https://coursera.org/research",
                category="Research",
                match_type="long_term",
                relevance_score=95,
                why_it_matches="Covers scientific evidence and PubMed methodology.",
                where_it_fits="Prepares for Month 7 Research milestone."
            )
        ]

        subject, html, txt = self.emailer.build_daily_alert(focus, learn_now, long_term)

        self.assertIn("General Chemistry", subject)
        self.assertIn("Atomic Structure", html)
        self.assertIn("Khan Academy", html)
        self.assertIn("Coursera", html)
        self.assertIn("Directly covers electron configurations", txt)
        self.assertIn("Prepares for Month 7 Research milestone", txt)

    def test_build_daily_alert_template_empty_recommendations_fallback(self):
        focus = self.calendar.get_learning_focus(month=1, week=2)
        subject, html, txt = self.emailer.build_daily_alert(focus, [], [])

        self.assertIn("General Chemistry", subject)
        self.assertIn("Right on track", html)
        self.assertIn("No urgent supplementary resources required today", txt)
        self.assertIn(focus.daily_focus, txt)

    def test_cli_daily_alert_preview(self):
        with patch.object(sys, 'argv', ['preuni', 'daily-alert', '--month', '1', '--week', '2', '--preview']):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)


if __name__ == "__main__":
    unittest.main()
