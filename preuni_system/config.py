"""
Configuration module for the Pre-University System.
Handles student profile, Resend email settings, SMTP fallback, scoring thresholds, and paths.
"""

import os
from pathlib import Path
from typing import Any, Dict

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
EMAIL_OUTPUT_DIR = OUTPUT_DIR / "emails"
CURRICULUM_DIR = BASE_DIR / "curriculum"
DASHBOARD_DIR = BASE_DIR / "dashboard"
TEMPLATES_DIR = BASE_DIR / "email_templates"
DATABASE_PATH = BASE_DIR / "preuni_system.sqlite3"

# Ensure runtime directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EMAIL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_dotenv(dotenv_path: Path = BASE_DIR / ".env") -> None:
    """Simple zero-dependency .env file parser."""
    if not dotenv_path.is_file():
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("\"'")
            if key not in os.environ:
                os.environ[key] = val


# Load .env if present
load_dotenv()


class Config:
    """System configuration container."""

    # Student Profile
    STUDENT_NAME: str = os.getenv("STUDENT_NAME", "Lara")
    STUDENT_EMAIL: str = os.getenv("STUDENT_EMAIL", "lara@example.com")
    PARENT_EMAIL: str = os.getenv("PARENT_EMAIL", "parent@example.com")
    COUNTRY: str = os.getenv("COUNTRY", "Nigeria")
    STATE: str = os.getenv("STATE", "Edo")
    CITY: str = os.getenv("CITY", "Benin City")
    UNIVERSITY: str = os.getenv("UNIVERSITY", "University of Benin (UNIBEN)")
    TARGET_FIELD: str = os.getenv("TARGET_FIELD", "Healthcare / Medical Sciences")
    PRIMARY_CAREER_INTEREST: str = os.getenv("PRIMARY_CAREER_INTEREST", "Nursing Science")
    CURRENT_APPRENTICESHIP: str = os.getenv("CURRENT_APPRENTICESHIP", "Tailoring & Fashion Design")
    TARGET_UNIVERSITY_DATE: str = os.getenv("TARGET_UNIVERSITY_DATE", "October 2027")
    TIMEZONE: str = os.getenv("TIMEZONE", "Africa/Lagos")

    # Study levels from lowest to highest; opportunities declare min_level/max_level on this scale.
    # STUDENT_LEVEL is where the student is now (change to "100L" after admission).
    STUDY_LEVELS = ["secondary", "pre-university", "100L", "200L", "300L+", "postgraduate"]
    STUDENT_LEVEL: str = os.getenv("STUDENT_LEVEL", "pre-university")

    # Time Commitments
    MAX_WEEKLY_HOURS: int = int(os.getenv("MAX_WEEKLY_HOURS", "18"))
    MAX_SIMULTANEOUS_COURSES: int = int(os.getenv("MAX_SIMULTANEOUS_COURSES", "2"))
    MAX_PAID_COURSE_COST: float = float(os.getenv("MAX_PAID_COURSE_COST", "0.0"))

    # Resend API Configuration
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_API_URL: str = os.getenv("RESEND_API_URL", "https://api.resend.com/emails")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "Pre-University System <onboarding@resend.dev>")

    # Fallback SMTP Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.resend.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "resend")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"))

    # Opportunity Quality Scoring Weights (Sum to 1.00)
    SCORING_WEIGHTS: Dict[str, float] = {
        "relevance": 0.25,
        "credibility": 0.20,
        "educational_value": 0.20,
        "cost_value": 0.10,
        "accessibility": 0.10,
        "age_suitability": 0.05,
        "time_commitment": 0.05,
        "networking": 0.05,
    }

    # Calendar & Daily Alert Configuration
    START_DATE: str = os.getenv("START_DATE", "2026-09-01")
    DAILY_ALERT_ENABLED: bool = os.getenv("DAILY_ALERT_ENABLED", "true").lower() in ("true", "1", "yes")
    MAX_LEARN_NOW_RECOMMENDATIONS: int = int(os.getenv("MAX_LEARN_NOW_RECOMMENDATIONS", "2"))
    MAX_LONG_TERM_RECOMMENDATIONS: int = int(os.getenv("MAX_LONG_TERM_RECOMMENDATIONS", "1"))
    MIN_DAILY_ALERT_RELEVANCE_SCORE: int = int(os.getenv("MIN_DAILY_ALERT_RELEVANCE_SCORE", "70"))
    LOOKBACK_DAYS_FOR_NEW_OPPS: int = int(os.getenv("LOOKBACK_DAYS_FOR_NEW_OPPS", "14"))

    # Daily Alert Relevance Weights (Sum to 1.00)
    DAILY_RELEVANCE_WEIGHTS: Dict[str, float] = {
        "topic_match": 0.35,
        "module_match": 0.20,
        "field_match": 0.20,
        "long_term_fit": 0.10,
        "quality": 0.10,
        "recency": 0.05,
    }

    # Thresholds
    ALERT_SCORE_THRESHOLD: int = int(os.getenv("ALERT_SCORE_THRESHOLD", "85"))
    CONSIDER_SCORE_THRESHOLD: int = int(os.getenv("CONSIDER_SCORE_THRESHOLD", "70"))

    # Geographic Priorities
    GEO_PRIORITIES = {
        "A": "Benin City / Edo State (Physical)",
        "B": "Nigeria (National)",
        "C": "Online / Global (Available to Nigerians)",
        "D": "International Physical (High-barrier)",
    }

    @classmethod
    def as_dict(cls) -> Dict[str, Any]:
        """Return config as dictionary for templating and reporting."""
        return {
            "student_name": cls.STUDENT_NAME,
            "student_email": cls.STUDENT_EMAIL,
            "parent_email": cls.PARENT_EMAIL,
            "country": cls.COUNTRY,
            "state": cls.STATE,
            "city": cls.CITY,
            "university": cls.UNIVERSITY,
            "target_field": cls.TARGET_FIELD,
            "primary_career": cls.PRIMARY_CAREER_INTEREST,
            "apprenticeship": cls.CURRENT_APPRENTICESHIP,
            "target_date": cls.TARGET_UNIVERSITY_DATE,
            "student_level": cls.STUDENT_LEVEL,
            "start_date": cls.START_DATE,
            "timezone": cls.TIMEZONE,
            "alert_threshold": cls.ALERT_SCORE_THRESHOLD,
            "daily_alert_enabled": cls.DAILY_ALERT_ENABLED,
            "resend_enabled": bool(cls.RESEND_API_KEY),
        }
