"""
Database manager for SQLite persistence, seed loading, queries, and state management.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from preuni_system.config import DATABASE_PATH, DATA_DIR
from preuni_system.models import (
    Course,
    VolunteeringOpportunity,
    HealthcareCareer,
    Opportunity,
    ReadingItem,
    SoftSkillAssessment,
)


class Database:
    """SQLite Database Interface."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database schema tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Courses Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT NOT NULL,
                cost TEXT DEFAULT 'Free',
                certificate INTEGER DEFAULT 0,
                duration TEXT DEFAULT '4 weeks',
                difficulty TEXT DEFAULT 'Beginner',
                eligibility TEXT,
                age_suitability TEXT,
                scores_json TEXT,
                total_score INTEGER DEFAULT 80,
                recommended_month INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Not started',
                practical_assignment TEXT,
                notes TEXT,
                created_at TEXT
            )
            """)

            # Volunteering Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS volunteering (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                organization TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL,
                location TEXT,
                geographic_priority TEXT DEFAULT 'A',
                date TEXT,
                deadline TEXT,
                age_requirement TEXT DEFAULT '16+',
                cost TEXT DEFAULT 'Free',
                time_commitment_hours INTEGER DEFAULT 4,
                skills_gained_json TEXT,
                safety_score INTEGER DEFAULT 95,
                credibility_score INTEGER DEFAULT 95,
                relevance_score INTEGER DEFAULT 90,
                overall_score INTEGER DEFAULT 90,
                parent_approval_required INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Available',
                hours_completed INTEGER DEFAULT 0,
                reflection TEXT,
                contact_info_json TEXT,
                created_at TEXT
            )
            """)

            # Healthcare Careers Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS healthcare_careers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                degree_name TEXT NOT NULL,
                overview TEXT,
                responsibilities_json TEXT,
                uniben_faculty_dept TEXT,
                duration_years INTEGER DEFAULT 5,
                utme_subjects_json TEXT,
                olevel_requirements TEXT,
                post_utme_profile TEXT,
                clinical_rotations TEXT,
                regulatory_body TEXT,
                career_progression_json TEXT,
                specializations_json TEXT,
                work_environments_json TEXT,
                challenges_json TEXT,
                international_mobility TEXT,
                entrepreneurial_possibilities_json TEXT
            )
            """)

            # Opportunities Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                organizer TEXT NOT NULL,
                category TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                location TEXT,
                date TEXT,
                deadline TEXT,
                cost TEXT DEFAULT 'Free',
                eligibility TEXT,
                geographic_priority TEXT DEFAULT 'A',
                scores_json TEXT,
                total_score INTEGER DEFAULT 80,
                is_immediate_alert INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                tags_json TEXT,
                created_at TEXT
            )
            """)

            # Reading List Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reading_list (
                id TEXT PRIMARY KEY,
                month INTEGER NOT NULL,
                week INTEGER NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                genre TEXT NOT NULL,
                url TEXT,
                summary TEXT,
                key_concepts_json TEXT,
                reflection_questions_json TEXT,
                practical_exercise TEXT,
                status TEXT DEFAULT 'Not read'
            )
            """)

            # Soft Skills Assessments Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS soft_skills (
                id TEXT PRIMARY KEY,
                quarter INTEGER NOT NULL,
                date TEXT NOT NULL,
                communication INTEGER DEFAULT 3,
                confidence INTEGER DEFAULT 3,
                critical_thinking INTEGER DEFAULT 3,
                emotional_intelligence INTEGER DEFAULT 3,
                time_management INTEGER DEFAULT 3,
                problem_solving INTEGER DEFAULT 3,
                teamwork INTEGER DEFAULT 3,
                leadership INTEGER DEFAULT 3,
                financial_discipline INTEGER DEFAULT 3,
                digital_literacy INTEGER DEFAULT 3,
                professionalism INTEGER DEFAULT 3,
                resilience INTEGER DEFAULT 3,
                creativity INTEGER DEFAULT 3,
                self_advocacy INTEGER DEFAULT 3,
                learning_ability INTEGER DEFAULT 3,
                evidence_notes TEXT
            )
            """)

            # Tailoring & Student Milestones Log Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tailoring_projects (
                id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                garment_type TEXT NOT NULL,
                date_started TEXT,
                date_completed TEXT,
                material_cost_ngn REAL DEFAULT 0.0,
                labor_cost_ngn REAL DEFAULT 0.0,
                selling_price_ngn REAL DEFAULT 0.0,
                profit_ngn REAL DEFAULT 0.0,
                customer_name TEXT,
                skills_practiced TEXT,
                photos_json TEXT,
                notes TEXT,
                status TEXT DEFAULT 'In Progress'
            )
            """)

            conn.commit()

    def seed_from_json(self) -> Dict[str, int]:
        """Load JSON seed files from data/ directory into SQLite database."""
        stats = {"courses": 0, "volunteering": 0, "careers": 0, "scholarships": 0, "reading": 0}

        # 1. Courses
        courses_file = DATA_DIR / "courses.json"
        if courses_file.is_file():
            with open(courses_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    for item in data:
                        scores = item.get("scores", {})
                        total_score = scores.get("total_score", 85)
                        cursor.execute("""
                        INSERT OR REPLACE INTO courses (
                            id, name, provider, url, category, cost, certificate, duration, difficulty,
                            eligibility, age_suitability, scores_json, total_score, recommended_month,
                            status, practical_assignment, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item["id"], item["name"], item["provider"], item["url"], item["category"],
                            item.get("cost", "Free"), 1 if item.get("certificate") else 0,
                            item.get("duration", "4 weeks"), item.get("difficulty", "Beginner"),
                            item.get("eligibility", "Open to all"), item.get("age_suitability", "Suitable"),
                            json.dumps(scores), total_score, item.get("recommended_month", 1),
                            item.get("status", "Not started"), item.get("practical_assignment", ""),
                            item.get("notes", ""), item.get("created_at", "")
                        ))
                        stats["courses"] += 1
                    conn.commit()

        # 2. Volunteering
        vol_file = DATA_DIR / "volunteering.json"
        if vol_file.is_file():
            with open(vol_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    for item in data:
                        cursor.execute("""
                        INSERT OR REPLACE INTO volunteering (
                            id, name, organization, category, description, url, location,
                            geographic_priority, date, deadline, age_requirement, cost,
                            time_commitment_hours, skills_gained_json, safety_score, credibility_score,
                            relevance_score, overall_score, parent_approval_required, status,
                            hours_completed, reflection, contact_info_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item["id"], item["name"], item["organization"], item["category"],
                            item.get("description", ""), item["url"], item.get("location", ""),
                            item.get("geographic_priority", "A"), item.get("date", "Ongoing"),
                            item.get("deadline"), item.get("age_requirement", "16+"),
                            item.get("cost", "Free"), item.get("time_commitment_hours", 4),
                            json.dumps(item.get("skills_gained", [])), item.get("safety_score", 95),
                            item.get("credibility_score", 95), item.get("relevance_score", 90),
                            item.get("overall_score", 90), 1 if item.get("parent_approval_required", True) else 0,
                            item.get("status", "Available"), item.get("hours_completed", 0),
                            item.get("reflection", ""), json.dumps(item.get("contact_info", {})),
                            item.get("created_at", "")
                        ))
                        stats["volunteering"] += 1
                    conn.commit()

        # 3. Healthcare Careers
        careers_file = DATA_DIR / "healthcare_careers.json"
        if careers_file.is_file():
            with open(careers_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    for item in data:
                        cursor.execute("""
                        INSERT OR REPLACE INTO healthcare_careers (
                            id, title, degree_name, overview, responsibilities_json,
                            uniben_faculty_dept, duration_years, utme_subjects_json,
                            olevel_requirements, post_utme_profile, clinical_rotations,
                            regulatory_body, career_progression_json, specializations_json,
                            work_environments_json, challenges_json, international_mobility,
                            entrepreneurial_possibilities_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item["id"], item["title"], item["degree_name"], item.get("overview", ""),
                            json.dumps(item.get("responsibilities", [])), item.get("uniben_faculty_dept", ""),
                            item.get("duration_years", 5), json.dumps(item.get("utme_subjects", [])),
                            item.get("olevel_requirements", ""), item.get("post_utme_profile", ""),
                            item.get("clinical_rotations", ""), item.get("regulatory_body", ""),
                            json.dumps(item.get("career_progression", [])),
                            json.dumps(item.get("specializations", [])),
                            json.dumps(item.get("work_environments", [])),
                            json.dumps(item.get("challenges", [])),
                            item.get("international_mobility", "High"),
                            json.dumps(item.get("entrepreneurial_possibilities", []))
                        ))
                        stats["careers"] += 1
                    conn.commit()

        # 4. Scholarships & Opportunities
        opps_file = DATA_DIR / "scholarships_competitions.json"
        if opps_file.is_file():
            with open(opps_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    for item in data:
                        scores = item.get("scores", {})
                        cursor.execute("""
                        INSERT OR REPLACE INTO opportunities (
                            id, title, organizer, category, url, description, location,
                            date, deadline, cost, eligibility, geographic_priority, scores_json,
                            total_score, is_immediate_alert, is_active, tags_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item["id"], item["title"], item["organizer"], item["category"],
                            item["url"], item.get("description", ""), item.get("location", ""),
                            item.get("date", ""), item.get("deadline"), item.get("cost", "Free"),
                            item.get("eligibility", ""), item.get("geographic_priority", "A"),
                            json.dumps(scores), item.get("total_score", 85),
                            1 if item.get("is_immediate_alert") else 0,
                            1 if item.get("is_active", True) else 0,
                            json.dumps(item.get("tags", [])), item.get("created_at", "")
                        ))
                        stats["scholarships"] += 1
                    conn.commit()

        # 5. Reading List
        reading_file = DATA_DIR / "reading_list.json"
        if reading_file.is_file():
            with open(reading_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    for item in data:
                        cursor.execute("""
                        INSERT OR REPLACE INTO reading_list (
                            id, month, week, title, author, genre, url, summary,
                            key_concepts_json, reflection_questions_json, practical_exercise, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            item["id"], item["month"], item.get("week", 1), item["title"], item["author"],
                            item.get("genre", ""), item.get("url", ""), item.get("summary", ""),
                            json.dumps(item.get("key_concepts", [])),
                            json.dumps(item.get("reflection_questions", [])),
                            item.get("practical_exercise", ""), item.get("status", "Not read")
                        ))
                        stats["reading"] += 1
                    conn.commit()

        return stats

    def get_courses(self, category: Optional[str] = None, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve courses with optional category or month filter."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM courses WHERE 1=1"
            params = []
            if category:
                query += " AND category LIKE ?"
                params.append(f"%{category}%")
            if month:
                query += " AND recommended_month = ?"
                params.append(month)
            query += " ORDER BY recommended_month ASC, total_score DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_volunteering(self, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve volunteering opportunities."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM volunteering WHERE 1=1"
            params = []
            if priority:
                query += " AND geographic_priority = ?"
                params.append(priority)
            query += " ORDER BY overall_score DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_top_opportunities(self, limit: int = 10, min_score: int = 70) -> List[Dict[str, Any]]:
        """Retrieve top active opportunities for digest."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM opportunities
            WHERE is_active = 1 AND total_score >= ?
            ORDER BY is_immediate_alert DESC, total_score DESC, deadline ASC
            LIMIT ?
            """, (min_score, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_healthcare_careers(self) -> List[Dict[str, Any]]:
        """Retrieve all healthcare career comparison profiles."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM healthcare_careers ORDER BY duration_years DESC, title ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_reading_items(self, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve reading curriculum items."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM reading_list WHERE 1=1"
            params = []
            if month:
                query += " AND month = ?"
                params.append(month)
            query += " ORDER BY month ASC, week ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_course_status(self, course_id: str, status: str) -> bool:
        """Update progress status of a course."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE courses SET status = ? WHERE id = ?", (status, course_id))
            conn.commit()
            return cursor.rowcount > 0

    def log_volunteering_hours(self, vol_id: str, hours: int, reflection: str = "") -> bool:
        """Log completed volunteer hours and personal reflection."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE volunteering
            SET hours_completed = hours_completed + ?, reflection = CASE WHEN reflection = '' THEN ? ELSE reflection || '\n' || ? END, status = 'Active'
            WHERE id = ?
            """, (hours, reflection, reflection, vol_id))
            conn.commit()
            return cursor.rowcount > 0

    def add_tailoring_project(self, project: Dict[str, Any]) -> str:
        """Log a completed or in-progress tailoring project with financial costing."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO tailoring_projects (
                id, project_name, garment_type, date_started, date_completed,
                material_cost_ngn, labor_cost_ngn, selling_price_ngn, profit_ngn,
                customer_name, skills_practiced, notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project["id"], project["project_name"], project["garment_type"],
                project.get("date_started"), project.get("date_completed"),
                project.get("material_cost_ngn", 0.0), project.get("labor_cost_ngn", 0.0),
                project.get("selling_price_ngn", 0.0), project.get("profit_ngn", 0.0),
                project.get("customer_name", ""), project.get("skills_practiced", ""),
                project.get("notes", ""), project.get("status", "Completed")
            ))
            conn.commit()
            return project["id"]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Aggregate summary metrics across all development areas."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END), SUM(CASE WHEN status='In progress' THEN 1 ELSE 0 END) FROM courses")
            courses_total, courses_done, courses_in_prog = cursor.fetchone()

            cursor.execute("SELECT COUNT(*), SUM(hours_completed) FROM volunteering")
            vol_orgs_count, vol_hours = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM healthcare_careers")
            careers_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM opportunities WHERE is_active=1")
            active_opps_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*), SUM(profit_ngn) FROM tailoring_projects WHERE status='Completed'")
            tailoring_count, tailoring_profit = cursor.fetchone()

            return {
                "courses_total": courses_total or 0,
                "courses_completed": courses_done or 0,
                "courses_in_progress": courses_in_prog or 0,
                "volunteering_orgs": vol_orgs_count or 0,
                "volunteering_hours": vol_hours or 0,
                "careers_explored": careers_count or 0,
                "active_opportunities": active_opps_count or 0,
                "tailoring_projects_completed": tailoring_count or 0,
                "tailoring_net_profit_ngn": tailoring_profit or 0.0,
            }
