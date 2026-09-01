"""
Unit tests for data models.
"""

import unittest
from preuni_system.models import (
    Course,
    VolunteeringOpportunity,
    HealthcareCareer,
    Opportunity,
    ReadingItem,
    SoftSkillAssessment,
)


class TestModels(unittest.TestCase):

    def test_course_creation(self):
        c = Course(
            id="crs-test-01",
            name="Test Biology Course",
            provider="Khan Academy",
            url="https://khanacademy.org",
            category="Academic Preparation - Biology",
            recommended_month=1
        )
        self.assertEqual(c.id, "crs-test-01")
        self.assertEqual(c.cost, "Free")
        self.assertEqual(c.status, "Not started")
        d = c.to_dict()
        self.assertEqual(d["name"], "Test Biology Course")

    def test_volunteering_model(self):
        v = VolunteeringOpportunity(
            id="vol-test-01",
            name="Red Cross Youth First Aid",
            organization="Nigerian Red Cross Society",
            category="Healthcare",
            description="First aid community training",
            url="https://nrcsvdb.org",
            location="Benin City, Edo State",
            geographic_priority="A"
        )
        self.assertEqual(v.geographic_priority, "A")
        self.assertTrue(v.parent_approval_required)
        self.assertEqual(v.safety_score, 95)

    def test_healthcare_career_model(self):
        car = HealthcareCareer(
            id="car-test-01",
            title="Nursing Science",
            degree_name="B.N.Sc",
            overview="Patient care and clinical advocacy",
            duration_years=5
        )
        self.assertEqual(car.duration_years, 5)
        self.assertIn("English", car.utme_subjects)


if __name__ == "__main__":
    unittest.main()
