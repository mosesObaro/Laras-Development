"""
Unit tests for database management and CGPA mathematics.
"""

import unittest
from pathlib import Path
import tempfile
from preuni_system.db import Database
from preuni_system.utils import calculate_uniben_cgpa, format_naira


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.db = Database(db_path=Path(self.temp_db_file.name))

    def test_database_initialization_and_seeding(self):
        stats = self.db.seed_from_json()
        self.assertGreaterEqual(stats["courses"], 50)
        self.assertGreaterEqual(stats["volunteering"], 10)
        self.assertGreaterEqual(stats["careers"], 10)

        courses = self.db.get_courses()
        self.assertGreater(len(courses), 0)

    def test_course_status_update(self):
        self.db.seed_from_json()
        courses = self.db.get_courses()
        first_id = courses[0]["id"]
        res = self.db.update_course_status(first_id, "Completed")
        self.assertTrue(res)

        updated_courses = self.db.get_courses()
        updated_first = next(c for c in updated_courses if c["id"] == first_id)
        self.assertEqual(updated_first["status"], "Completed")

    def test_uniben_cgpa_calculation(self):
        # 1st Semester:
        # BIO111 (3 units) Grade A (5 GP) -> 15
        # CHM111 (3 units) Grade A (5 GP) -> 15
        # PHY111 (3 units) Grade B (4 GP) -> 12
        # MTH111 (3 units) Grade B (4 GP) -> 12
        # GST111 (2 units) Grade A (5 GP) -> 10
        # Total units = 14, Points = 64 -> GPA = 64/14 = 4.57 (First Class)
        grades = [
            ("BIO111", 3, 75), # A = 5
            ("CHM111", 3, 72), # A = 5
            ("PHY111", 3, 65), # B = 4
            ("MTH111", 3, 62), # B = 4
            ("GST111", 2, 80), # A = 5
        ]
        result = calculate_uniben_cgpa(grades)
        self.assertEqual(result["total_units"], 14)
        self.assertEqual(result["total_weighted_points"], 64)
        self.assertEqual(result["cgpa"], 4.57)
        self.assertEqual(result["classification"], "First Class Honours")


if __name__ == "__main__":
    unittest.main()
