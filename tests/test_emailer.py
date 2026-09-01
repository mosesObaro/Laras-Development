"""
Unit tests for email templates and Resend delivery logic.
"""

import unittest
from preuni_system.emailer import EmailService


class TestEmailer(unittest.TestCase):

    def setUp(self):
        self.emailer = EmailService()

    def test_immediate_alert_template_builder(self):
        opp = {
            "id": "opp-test-01",
            "title": "Seplat Energy PEARLs Scholarship",
            "organizer": "Seplat Energy",
            "category": "Scholarship",
            "total_score": 99,
            "deadline": "2027-08-31",
            "location": "Edo State",
            "cost": "Free",
            "eligibility": "Edo/Delta Undergraduates",
            "url": "https://seplatenergy.com",
            "description": "Tuition grant for healthcare undergraduates"
        }
        subject, html, txt = self.emailer.build_immediate_alert(opp)
        self.assertIn("99/100", subject)
        self.assertIn("Seplat Energy", html)
        self.assertIn("Seplat Energy", txt)
        self.assertIn("https://seplatenergy.com", html)

    def test_weekly_digest_template_builder(self):
        opps = [{
            "title": "Red Cross Youth Health Training",
            "organizer": "Nigerian Red Cross",
            "total_score": 98,
            "deadline": "Ongoing",
            "url": "https://nrcsvdb.org",
            "description": "Community first aid sensitization in Benin City"
        }]
        courses = [{
            "name": "High School Biology",
            "provider": "Khan Academy",
            "duration": "6 weeks",
            "practical_assignment": "Sketch nephron diagram",
            "url": "https://khanacademy.org"
        }]
        reading = {
            "title": "Atomic Habits",
            "author": "James Clear",
            "practical_exercise": "Apply 2-minute rule"
        }

        subject, html, txt = self.emailer.build_weekly_digest(1, 1, opps, courses, reading)
        self.assertIn("Month 1, Week 1", subject)
        self.assertIn("Atomic Habits", html)
        self.assertIn("Red Cross", txt)

    def test_dry_run_dispatch(self):
        subject, html, txt = self.emailer.build_weekly_digest(1, 1, [], [])
        res = self.emailer.dispatch_email(subject, html, txt, dry_run=True, file_tag="test_digest")
        self.assertTrue(res["success"])
        self.assertEqual(res["mode"], "dry_run / preview")
        self.assertTrue(res["preview_html"].endswith(".html"))


if __name__ == "__main__":
    unittest.main()
