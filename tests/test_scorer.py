"""
Unit tests for opportunity scoring and safety evaluation.
"""

import unittest
from preuni_system.scorer import OpportunityScorer


class TestScorer(unittest.TestCase):

    def test_weighted_scoring_strongly_recommended(self):
        sub_scores = {
            "relevance": 95,
            "credibility": 95,
            "educational_value": 90,
            "cost_value": 100,
            "accessibility": 90,
            "age_suitability": 95,
            "time_commitment": 90,
            "networking": 85,
        }
        score, recommendation = OpportunityScorer.calculate_quality_score(sub_scores)
        self.assertGreaterEqual(score, 85)
        self.assertEqual(recommendation, "STRONGLY RECOMMENDED")

    def test_weighted_scoring_consider_and_suppressed(self):
        # Consider (70 - 84)
        sub_scores_mid = {
            "relevance": 75, "credibility": 75, "educational_value": 70,
            "cost_value": 80, "accessibility": 80, "age_suitability": 70,
            "time_commitment": 70, "networking": 60
        }
        score_mid, rec_mid = OpportunityScorer.calculate_quality_score(sub_scores_mid)
        self.assertTrue(70 <= score_mid <= 84)
        self.assertEqual(rec_mid, "CONSIDER")

        # Suppressed (< 70)
        sub_scores_low = {
            "relevance": 40, "credibility": 50, "educational_value": 40,
            "cost_value": 50, "accessibility": 50, "age_suitability": 50,
            "time_commitment": 50, "networking": 40
        }
        score_low, rec_low = OpportunityScorer.calculate_quality_score(sub_scores_low)
        self.assertLess(score_low, 70)
        self.assertEqual(rec_low, "SUPPRESSED")

    def test_safety_check_clinical_procedure_rejection(self):
        # Teenager must NOT perform clinical invasive procedures
        unsafe_opp = {
            "title": "Volunteer to administer injections and draw blood",
            "description": "Volunteers will inject patients and perform surgery under basic supervision",
            "organization": "Unknown Clinic",
            "cost": "Free"
        }
        safety = OpportunityScorer.evaluate_safety(unsafe_opp)
        self.assertFalse(safety["is_safe"])
        self.assertGreater(len(safety["red_flags"]), 0)

    def test_safety_check_credible_organization(self):
        safe_opp = {
            "title": "Community Health Hygiene Sensitization",
            "description": "Assist with public health flyer distribution and handwashing education",
            "organization": "Nigerian Red Cross Society",
            "cost": "Free"
        }
        safety = OpportunityScorer.evaluate_safety(safe_opp)
        self.assertTrue(safety["is_safe"])
        self.assertEqual(safety["safety_score"], 98)


if __name__ == "__main__":
    unittest.main()
