"""
Unit tests for the Learning Calendar Engine.
"""

import unittest
from datetime import date, timedelta
from preuni_system.calendar import LearningCalendarEngine


class TestLearningCalendar(unittest.TestCase):

    def setUp(self):
        self.calendar = LearningCalendarEngine(start_date_str="2026-09-01")

    def test_week_calculation_from_start_date(self):
        # Day 0 (2026-09-01) -> Week 1
        w1 = self.calendar.calculate_week_number("2026-09-01")
        self.assertEqual(w1, 1)

        # Day 7 (2026-09-08) -> Week 2
        w2 = self.calendar.calculate_week_number("2026-09-08")
        self.assertEqual(w2, 2)

        # Date prior to start_date -> Week 1
        w_early = self.calendar.calculate_week_number("2026-08-15")
        self.assertEqual(w_early, 1)

        # High week clamping
        w_far = self.calendar.calculate_week_number("2030-01-01")
        self.assertEqual(w_far, 78)

    def test_get_learning_focus_month_week_override(self):
        focus = self.calendar.get_learning_focus(month=1, week=1)
        self.assertEqual(focus.month, 1)
        self.assertEqual(focus.week_in_month, 1)
        self.assertEqual(focus.global_week, 1)
        self.assertEqual(focus.subject, "Biology & Study Systems")
        self.assertIn("Cell Structure", focus.topic)
        self.assertTrue(len(focus.weekly_objectives) > 0)
        self.assertTrue(len(focus.daily_focus) > 0)

    def test_get_learning_focus_phase_transitions(self):
        # Month 1 -> Phase 1
        f1 = self.calendar.get_learning_focus(month=1, week=1)
        self.assertIn("Phase 1", f1.phase)

        # Month 7 -> Phase 2
        f7 = self.calendar.get_learning_focus(month=7, week=1)
        self.assertIn("Phase 2", f7.phase)
        self.assertIn("Research", f7.subject)

        # Month 14 -> Phase 3
        f14 = self.calendar.get_learning_focus(month=14, week=1)
        self.assertIn("Phase 3", f14.phase)
        self.assertIn("Medical Terminology", f14.subject)

    def test_upcoming_keywords_aggregation(self):
        kws = self.calendar.get_upcoming_keywords(current_global_week=1, lookahead_weeks=4)
        self.assertIsInstance(kws, list)
        self.assertTrue(len(kws) > 0)


if __name__ == "__main__":
    unittest.main()
