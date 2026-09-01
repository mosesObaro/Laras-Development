"""
Unit tests for opportunity crawler and URL validation.
"""

import unittest
from preuni_system.crawler import OpportunityCrawler
from preuni_system.utils import is_suspicious_url, parse_date, is_expired


class TestCrawler(unittest.TestCase):

    def setUp(self):
        self.crawler = OpportunityCrawler()

    def test_suspicious_url_detection(self):
        self.assertTrue(is_suspicious_url("https://tinyurl.com/free-money-now"))
        self.assertTrue(is_suspicious_url("https://t.me/joinchat/12345"))
        self.assertTrue(is_suspicious_url("https://crypto-gift.io"))
        self.assertFalse(is_suspicious_url("https://openwho.org/courses/IPC"))
        self.assertFalse(is_suspicious_url("https://coursera.org/learn/vital-signs"))

    def test_date_parsing_and_expiry(self):
        d1 = parse_date("2027-12-31")
        self.assertIsNotNone(d1)
        self.assertFalse(is_expired("2030-01-01"))
        self.assertTrue(is_expired("2020-01-01"))

    def test_clean_and_score_item(self):
        raw = {
            "title": "NNPC Healthcare Scholarship for Undergraduates",
            "url": "https://nnpcgroup.com/scholarships",
            "description": "Annual scholarship for Nigerian students studying medicine and nursing in federal universities.",
            "organizer": "NNPC",
            "cost": "Free",
            "deadline": "2027-10-31"
        }
        scored = self.crawler.clean_and_score_item(raw, default_category="Scholarship")
        self.assertIsNotNone(scored)
        self.assertEqual(scored["category"], "Scholarship")
        self.assertGreaterEqual(scored["total_score"], 80)


if __name__ == "__main__":
    unittest.main()
