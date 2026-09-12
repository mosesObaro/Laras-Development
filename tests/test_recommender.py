"""
Unit tests for Personalized Learning Recommender Engine.
"""

import unittest
from preuni_system.calendar import LearningCalendarEngine
from preuni_system.recommender import PersonalizedLearningRecommender
from preuni_system.utils import normalize_url


class TestRecommender(unittest.TestCase):

    def setUp(self):
        self.calendar = LearningCalendarEngine(start_date_str="2026-09-01")
        self.recommender = PersonalizedLearningRecommender()

        self.candidates = [
            {
                "id": "crs-test-bio-1",
                "title": "High School Biology: Cell Membranes and Cellular Transport",
                "provider": "Khan Academy",
                "url": "https://khanacademy.org/bio-cells",
                "category": "Academic Preparation - Biology",
                "resource_type": "Course",
                "description": "Cell structure, osmosis, diffusion, and membrane proteins.",
                "practical_task": "Sketch cell membrane diagram.",
                "difficulty": "Beginner",
                "duration": "4 weeks",
                "cost": "Free",
                "recommended_month": 1,
                "total_score": 95,
            },
            {
                "id": "crs-test-chm-1",
                "title": "General Chemistry: Principles & Atomic Structure",
                "provider": "OpenStax",
                "url": "https://openstax.org/chemistry",
                "category": "Academic Preparation - Chemistry",
                "resource_type": "Course",
                "description": "Atoms, electrons, and periodic trends.",
                "practical_task": "Balance equations.",
                "difficulty": "Beginner",
                "duration": "6 weeks",
                "cost": "Free",
                "recommended_month": 2,
                "total_score": 92,
            },
            {
                "id": "crs-test-med-res",
                "title": "Introduction to Health Research Methodology & Clinical Ethics",
                "provider": "Stanford (Coursera)",
                "url": "https://coursera.org/health-research",
                "category": "Healthcare Foundations",
                "resource_type": "Course",
                "description": "Formulating PICO research questions and bioethics.",
                "practical_task": "Draft PICO proposal.",
                "difficulty": "Intermediate",
                "duration": "6 weeks",
                "cost": "Free",
                "recommended_month": 7,
                "total_score": 96,
            }
        ]

    def test_learn_now_relevance_matching(self):
        # Focus on Month 1, Week 1 (Cell Biology & Transport)
        focus = self.calendar.get_learning_focus(month=1, week=1)
        upcoming_kws = self.calendar.get_upcoming_keywords(focus.global_week)

        recs = self.recommender.rank_and_select_recommendations(
            candidates=self.candidates,
            learning_focus=focus,
            upcoming_keywords=upcoming_kws,
            already_alerted_urls=set(),
            completed_urls=set(),
            force=True
        )

        self.assertTrue(len(recs["learn_now"]) > 0)
        # Top Learn Now should be the Cell Biology course
        top_learn = recs["learn_now"][0]
        self.assertEqual(top_learn.opportunity_id, "crs-test-bio-1")
        self.assertIn("Cell", top_learn.title)
        self.assertEqual(top_learn.match_type, "learn_now")
        self.assertGreaterEqual(top_learn.relevance_score, 70)

    def test_long_term_match_separation(self):
        # Focus on Month 1, Week 1 (Cell Biology)
        focus = self.calendar.get_learning_focus(month=1, week=1)
        upcoming_kws = self.calendar.get_upcoming_keywords(focus.global_week)

        recs = self.recommender.rank_and_select_recommendations(
            candidates=self.candidates,
            learning_focus=focus,
            upcoming_keywords=upcoming_kws,
            already_alerted_urls=set(),
            completed_urls=set(),
            force=True
        )

        self.assertTrue(len(recs["long_term"]) > 0)
        top_lt = recs["long_term"][0]
        self.assertEqual(top_lt.match_type, "long_term")
        # Long term match should NOT be the same as Learn Now
        self.assertNotEqual(top_lt.opportunity_id, "crs-test-bio-1")
        self.assertTrue(len(top_lt.where_it_fits) > 0)
        self.assertIn("prepares for month", top_lt.where_it_fits.lower())

    def test_already_alerted_deduplication(self):
        focus = self.calendar.get_learning_focus(month=1, week=1)
        upcoming_kws = self.calendar.get_upcoming_keywords(focus.global_week)

        # Mark bio course as already alerted (including with trailing slash & tracking params)
        alerted = {normalize_url("https://khanacademy.org/bio-cells?utm_source=daily_alert&fbclid=123")}

        recs = self.recommender.rank_and_select_recommendations(
            candidates=self.candidates,
            learning_focus=focus,
            upcoming_keywords=upcoming_kws,
            already_alerted_urls=alerted,
            completed_urls=set(),
            force=False
        )

        # The alerted course must NOT be in learn_now
        for item in recs["learn_now"]:
            self.assertNotEqual(normalize_url(item.url), normalize_url("https://khanacademy.org/bio-cells"))

    def test_completed_course_suppression(self):
        focus = self.calendar.get_learning_focus(month=1, week=1)
        upcoming_kws = self.calendar.get_upcoming_keywords(focus.global_week)
        completed = {normalize_url("https://khanacademy.org/bio-cells")}

        recs = self.recommender.rank_and_select_recommendations(
            candidates=self.candidates,
            learning_focus=focus,
            upcoming_keywords=upcoming_kws,
            already_alerted_urls=set(),
            completed_urls=completed,
            force=False
        )

        for item in recs["learn_now"] + recs["long_term"]:
            self.assertNotEqual(normalize_url(item.url), normalize_url("https://khanacademy.org/bio-cells"))


if __name__ == "__main__":
    unittest.main()
